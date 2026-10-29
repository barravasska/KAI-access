"""YOLO face detector -> face alignment and ArcFace embedding (via InsightFace).

Demo implementation: the InsightFace model pack includes a second landmark
face detector run on the YOLO ROI. This is deliberately simpler and easier to
validate than mixing custom YOLO landmark tensor formats. Optimize only after
functional and accuracy tests pass.
"""
import os
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()


def compare_embeddings(probe, candidates, threshold=0.50, margin=0.04):
    """Compare normalized ArcFace embeddings grouped by user_id.

    IMPORTANT: threshold/margin are uncalibrated DEMO defaults, not a security
    guarantee. Never open a real gate based on this alone.
    """
    p = np.asarray(probe, dtype=np.float32)
    if p.shape != (512,) or not np.all(np.isfinite(p)):
        raise ValueError('Embedding scan harus berisi 512 angka finite')
    pnorm = np.linalg.norm(p)
    if pnorm < 1e-6:
        raise ValueError('Embedding scan kosong')
    p = p / pnorm
    best_per_user = {}
    for item in candidates:
        uid = str(item['user_id'])
        e = np.asarray(item['embedding'], dtype=np.float32)
        if e.shape != (512,) or not np.all(np.isfinite(e)):
            raise ValueError(f'Embedding tidak valid untuk {uid}')
        norm = np.linalg.norm(e)
        if norm < 1e-6:
            raise ValueError(f'Embedding nol untuk {uid}')
        score = float(np.dot(p, e / norm))
        best_per_user[uid] = max(best_per_user.get(uid, -1.0), score)
    ranking = sorted(best_per_user.items(), key=lambda x: x[1], reverse=True)
    if not ranking:
        return {'matched': False, 'user_id': None, 'similarity': None,
                'runner_up_similarity': None, 'reason': 'EMPTY_GALLERY'}
    uid, first = ranking[0]
    second = ranking[1][1] if len(ranking) > 1 else None
    accepted = first >= threshold and (second is None or first - second >= margin)
    return {'matched': bool(accepted), 'user_id': uid if accepted else None,
            'similarity': round(first, 4),
            'runner_up_similarity': round(second, 4) if second is not None else None,
            'reason': 'MATCH' if accepted else 'UNKNOWN_OR_AMBIGUOUS'}


class FaceEngine:
    def __init__(self):
        from ultralytics import YOLO
        from insightface.app import FaceAnalysis
        weights = Path(os.getenv('YOLO_WEIGHTS', 'models/yolov8n-face.pt'))
        if not weights.is_file():
            raise FileNotFoundError(f'Bobot YOLO tidak ditemukan: {weights}. Lihat README.md')
        self.yolo = YOLO(str(weights))
        # CPU is the safe cross-platform baseline. NVIDIA CUDA setup is optional.
        self.arcface = FaceAnalysis(
            name=os.getenv('ARCFACE_PACK', 'buffalo_l'),
            allowed_modules=['detection', 'recognition'],
            providers=['CPUExecutionProvider'])
        self.arcface.prepare(ctx_id=-1, det_size=(640, 640))
        self.min_size = int(os.getenv('MIN_FACE_SIZE', '90'))
        self.blur_threshold = float(os.getenv('BLUR_THRESHOLD', '10'))

    def embed(self, frame):
        if frame is None or frame.size == 0:
            return {'ok': False, 'reason': 'BAD_IMAGE'}
        result = self.yolo.predict(source=frame, conf=0.5,
                                   imgsz=640, verbose=False)[0]
        boxes = result.boxes
        count = 0 if boxes is None else len(boxes)
        if count != 1:
            return {'ok': False,
                    'reason': 'NO_FACE' if count == 0 else 'MULTIPLE_FACES',
                    'faces_detected': count}
        xyxy = boxes.xyxy[0].cpu().numpy().astype(int)
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in xyxy]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        fw, fh = x2 - x1, y2 - y1
        if fw < self.min_size or fh < self.min_size:
            return {'ok': False, 'reason': 'FACE_TOO_SMALL',
                    'box': [x1, y1, x2, y2]}
        face_crop = frame[y1:y2, x1:x2]
        grayscale = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        blur = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
        if blur < self.blur_threshold:
            return {'ok': False, 'reason': 'BLURRY',
                    'box': [x1, y1, x2, y2]}
        # Extra margin lets the recognizer detect its 5 alignment landmarks.
        padding = int(max(fw, fh) * 0.40)
        roi = frame[max(0, y1-padding):min(height, y2+padding),
                    max(0, x1-padding):min(width, x2+padding)]
        aligned_faces = self.arcface.get(roi)
        if len(aligned_faces) != 1:
            return {'ok': False, 'reason': 'LANDMARK_NOT_FOUND',
                    'box': [x1, y1, x2, y2]}
        embedding = getattr(aligned_faces[0], 'normed_embedding', None)
        if embedding is None:
            return {'ok': False, 'reason': 'EMBEDDING_FAILED'}
        vector = np.asarray(embedding, dtype=np.float32)
        if vector.shape != (512,):
            return {'ok': False, 'reason': 'WRONG_EMBEDDING_SIZE'}
        return {
    "ok": True,
    "reason": "OK",
    "embedding": vector.tolist(),
    "embedding_dimension": 512,
    "model_version": os.getenv(
        "MODEL_VERSION",
        "arcface-buffalo_l-v1"
    ),
    "box": [x1, y1, x2, y2],
    "faces_detected": 1,
    "blur_score": round(blur, 1)
}
