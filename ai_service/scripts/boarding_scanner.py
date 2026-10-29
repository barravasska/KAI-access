import json
import os
import time
from pathlib import Path

import cv2
import requests
from dotenv import load_dotenv

from src.face_engine import FaceEngine, compare_embeddings

load_dotenv()

BOARDING_URL = "http://127.0.0.1:8002/boarding/verify"

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.50"))
MATCH_MARGIN = float(os.getenv("MATCH_MARGIN", "0.04"))

SCAN_INTERVAL = 5
REQUIRED_STREAK = 3
COOLDOWN_SECONDS = 8


def verify_ticket(user_id, similarity):
    """Minta keputusan boarding dari mock backend."""
    try:
        response = requests.post(
            BOARDING_URL,
            json={
                "user_id": user_id,
                "similarity": similarity
            },
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") not in ("GRANTED", "DENIED"):
            return "ERROR", "INVALID_BACKEND_RESPONSE"

        return data["status"], data.get("reason", "")

    except (requests.RequestException, ValueError):
        return "ERROR", "BACKEND_UNAVAILABLE"


def main():
    gallery_path = Path("data/dev_gallery.json")

    if not gallery_path.exists():
        print("Gallery belum tersedia.")
        return

    gallery = json.loads(
        gallery_path.read_text(encoding="utf-8")
    )

    engine = FaceEngine()

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
    )

    if not camera.isOpened():
        print("Webcam tidak tersedia.")
        return

    frame_count = 0
    streak_user = None
    streak_count = 0
    display_label = "SCANNER READY"
    display_box = None
    color = (255, 180, 0)

    last_check = 0
    last_checked_user = None

    try:
        while True:
            ret, frame = camera.read()

            if not ret:
                break

            frame_count += 1

            if frame_count % SCAN_INTERVAL == 0:
                result = engine.embed(frame)
                display_box = result.get("box")

                if not result["ok"]:
                    display_label = result.get("reason", "INVALID_FACE")
                    color = (0, 200, 255)
                    streak_user = None
                    streak_count = 0
                    last_checked_user = None

                else:
                    decision = compare_embeddings(
                        result["embedding"],
                        gallery,
                        threshold=MATCH_THRESHOLD,
                        margin=MATCH_MARGIN
                    )

                    uid = (
                        decision["user_id"]
                        if decision["matched"]
                        else None
                    )

                    if uid is None:
                        display_label = "UNKNOWN FACE"
                        color = (0, 0, 255)
                        streak_user = None
                        streak_count = 0
                        last_checked_user = None

                    else:
                        if uid == streak_user:
                            streak_count += 1
                        else:
                            streak_user = uid
                            streak_count = 1

                        if streak_count < REQUIRED_STREAK:
                            display_label = "VERIFYING FACE..."
                            color = (0, 200, 255)

                        elif (
                            uid != last_checked_user
                            or time.monotonic() - last_check >= COOLDOWN_SECONDS
                        ):
                            status, reason = verify_ticket(
                                uid,
                                decision["similarity"]
                            )

                            display_label = f"{uid}: {status} - {reason}"

                            if status == "GRANTED":
                                color = (0, 200, 0)
                            elif status == "DENIED":
                                color = (0, 0, 255)
                            else:
                                color = (0, 200, 255)

                            last_check = time.monotonic()
                            last_checked_user = uid

            if display_box:
                x1, y1, x2, y2 = display_box

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

            cv2.putText(
                frame,
                display_label[:80],
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                color,
                2
            )

            cv2.imshow(
                "Smart Boarding Scanner - Sakha",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
