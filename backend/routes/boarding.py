
import os

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User, BoardingLog, FaceEmbedding, Train
from security import require_admin
from services.boarding_service import verify_boarding
from services.ai_client import generate_embedding, match_face


router = APIRouter(
    prefix="/api/boarding",
    tags=["Boarding Verification"]
)


# ======================================
# 1. MOCK BOARDING (DEVELOPMENT)
# ======================================

class MockBoardingRequest(BaseModel):
    user_id: int | None = None
    train_id: int = Field(gt=0)
    matched: bool
    similarity: float | None = Field(
        default=None, ge=-1, le=1
    )


@router.post("/dev-verify")
def dev_verify(
    data: MockBoardingRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    if os.getenv(
        "ENABLE_MOCK_BOARDING", "false"
    ).lower() != "true":
        raise HTTPException(
            status_code=404,
            detail="Endpoint simulasi dinonaktifkan"
        )

    return verify_boarding(
        db=db,
        user_id=data.user_id,
        train_id=data.train_id,
        matched=data.matched,
        similarity=data.similarity
    )


# ======================================
# 2. REAL AI BOARDING SCANNER
# ======================================

@router.post("/scan")
async def scan_boarding(
    train_id: int = Form(..., gt=0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    # Hanya admin yang boleh menjalankan scanner.

    train = db.get(Train, train_id)

    if train is None:
        raise HTTPException(
            status_code=404,
            detail="Jadwal kereta tidak ditemukan"
        )

    # AI Sakha mendukung JPEG dan PNG.
    if file.content_type not in (
        "image/jpeg", "image/png"
    ):
        raise HTTPException(
            status_code=415,
            detail="File harus JPEG atau PNG"
        )

    max_bytes = 4 * 1024 * 1024

    image_bytes = await file.read(max_bytes + 1)
    await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Frame kamera kosong"
        )

    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="Ukuran frame maksimal 4 MB"
        )

    # Langkah A:
    # YOLO + ArcFace mengubah frame
    # webcam menjadi embedding.
    ai_face = await generate_embedding(
        image_bytes,
        file.content_type
    )

    model_version = ai_face["model_version"]
    probe_embedding = ai_face["embedding"]

    # Langkah B:
    # Ambil embedding terdaftar yang dibuat
    # menggunakan versi model yang sama.
    faces = db.scalars(
        select(FaceEmbedding).where(
            FaceEmbedding.model_version == model_version
        )
    ).all()

    candidates = [
        {
            "user_id": face.user_id,
            "embedding": face.embedding
        }
        for face in faces
    ]

    # Langkah C:
    # Bandingkan embedding hasil webcam
    # dengan embedding dari MySQL.
    ai_match = await match_face(
        embedding_bytes=probe_embedding,
        candidates=candidates
    )

    # Langkah D:
    # Identitas hanya berasal dari AI,
    # bukan dari input manual browser.
    matched = ai_match["matched"]
    user_id = ai_match["user_id"]
    similarity = ai_match["similarity"]

    # Langkah E:
    # Verifikasi kepemilikan dan status tiket.
    boarding_result = verify_boarding(
        db=db,
        user_id=user_id,
        train_id=train_id,
        matched=matched,
        similarity=similarity
    )

    # Langkah F:
    # Kirim hasil untuk tampilan scanner.
    return {
        **boarding_result,
        "similarity": similarity,
        "ai_reason": ai_match.get("reason"),
        "bbox": ai_face.get("box"),
        "model_version": model_version
    }


# ======================================
# 3. BOARDING LOGS
# ======================================

@router.get("/logs")
def get_boarding_logs(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    logs = db.scalars(
        select(BoardingLog)
        .order_by(BoardingLog.id.desc())
        .limit(100)
    ).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "ticket_id": log.ticket_id,
            "scan_time": log.scan_time,
            "similarity": log.similarity,
            "result": log.result,
            "reason": log.reason
        }
        for log in logs
    ]
