"""Local-only demo gallery. Do not commit faces or embeddings to Git."""
import argparse
import json
from pathlib import Path

import cv2

from src.face_engine import FaceEngine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True, help='test user ID, not secret')
    parser.add_argument('--image', required=True, help='photo of consenting person')
    args = parser.parse_args()
    path = Path(args.image)
    image = cv2.imread(str(path))
    if image is None:
        raise SystemExit(f'Gambar tidak dapat dibuka: {path}')
    outcome = FaceEngine().embed(image)
    if not outcome['ok']:
        raise SystemExit(f'Gagal enroll: {outcome["reason"]}')
    gallery_path = Path('data/dev_gallery.json')
    gallery_path.parent.mkdir(parents=True, exist_ok=True)
    gallery = json.loads(gallery_path.read_text(encoding='utf-8')) if gallery_path.exists() else []
    gallery.append({'user_id': args.user, 'embedding': outcome['embedding']})
    gallery_path.write_text(json.dumps(gallery), encoding='utf-8')
    print(f'Berhasil menyimpan embedding demo user={args.user}. Total contoh: {len(gallery)}')


if __name__ == '__main__':
    main()
