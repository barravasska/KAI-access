"""Local recognition demo. Never interprets match as a VALID TICKET."""
import json
import os
from pathlib import Path

import cv2
from dotenv import load_dotenv

from src.face_engine import FaceEngine, compare_embeddings

load_dotenv()


def main():
    gallery_path = Path('data/dev_gallery.json')
    if not gallery_path.exists():
        raise SystemExit('Belum ada gallery. Jalankan scripts/local_enroll.py dulu.')
    gallery = json.loads(gallery_path.read_text(encoding='utf-8'))
    engine = FaceEngine()
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
    if not cam.isOpened():
        raise SystemExit('Webcam tidak tersedia. Coba indeks kamera 1.')
    frame_index = 0
    display_label = 'Starting...'
    display_box = None
    box_color = (255, 180, 0)
    streak_user = None
    streak_count = 0
    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                break
            frame_index += 1
            if frame_index % 5 == 0:
                result = engine.embed(frame)
                display_box = result.get('box')
                if not result['ok']:
                    display_label = result['reason']
                    box_color = (0, 165, 255)
                    streak_user, streak_count = None, 0
                else:
                    decision = compare_embeddings(
                        result['embedding'], gallery,
                        threshold=float(os.getenv('MATCH_THRESHOLD', '0.50')),
                        margin=float(os.getenv('MATCH_MARGIN', '0.04')))
                    uid = decision['user_id'] if decision['matched'] else None
                    sim_val = decision.get('similarity')
                    sim_str = f" ({sim_val:.2f})" if sim_val is not None else ""
                    if uid and uid == streak_user:
                        streak_count += 1
                    else:
                        streak_user, streak_count = uid, 1 if uid else 0
                    if uid and streak_count >= 2:
                        display_label = f'Wajah dikenali: {uid}{sim_str} | TIKET BELUM DICEK'
                        box_color = (0, 255, 0)
                    elif uid:
                        display_label = f'Memverifikasi wajah...{sim_str}'
                        box_color = (0, 255, 255)
                    else:
                        display_label = f'UNKNOWN{sim_str}'
                        box_color = (0, 0, 255)
            if display_box:
                x1, y1, x2, y2 = display_box
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(frame, display_label[:75], (10, 34),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, box_color, 2)
            cv2.imshow('Sakha - Face Recognition Demo (Q: keluar)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
