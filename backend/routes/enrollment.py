from io import BytesIO

from fastapi import (
    APIRouter, Depends, File,
    UploadFile, HTTPException
)

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User, FaceEmbedding
from security import get_current_user
from services.ai_client import generate_embedding

router = APIRouter(
    prefix="/api/face",
    tags=["Face Enrollment"]
)

MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/enroll")
async def enroll_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    existing_face = db.scalar(
        select(FaceEmbedding).where(
            FaceEmbedding.user_id == user.id
        )
    )
    if existing_face is not None:
        raise HTTPException(
            status_code=409,
            detail="Wajah sudah terdaftar. Hubungi admin jika ingin mendaftar ulang."
        )

    # Validasi tipe file
    if file.content_type not in [
        "image/jpeg",
        "image/png"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Gunakan gambar JPG atau PNG"
        )

    # Membatasi ukuran file
    image_bytes = await file.read(
        MAX_FILE_SIZE + 1
    )

    await file.close()

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Ukuran gambar maksimal 5 MB"
        )

    # Pastikan file benar-benar gambar
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            if img.format not in ("JPEG", "PNG"):
                raise ValueError("Format tidak didukung")

            img.verify()

        with Image.open(BytesIO(image_bytes)) as img:
            width, height = img.size

    except (
        UnidentifiedImageError,
        ValueError,
        OSError
    ):
        raise HTTPException(
            status_code=400,
            detail="File gambar tidak valid"
        )

    if width < 160 or height < 160:
        raise HTTPException(
            status_code=400,
            detail="Resolusi gambar terlalu kecil"
        )

    # Mengirim foto ke layanan AI Sakha
    ai_result = await generate_embedding(
    image_bytes,
    file.content_type
)

    # Menyimpan hasil embedding ke MySQL
    face_data = FaceEmbedding(
        user_id=user.id,
        embedding=ai_result["embedding"],
        model_version=ai_result["model_version"]
    )

    try:
        db.add(face_data)
        db.commit()
        db.refresh(face_data)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Gagal menyimpan data wajah"
        )

    return {
        "message": "Registrasi wajah berhasil",
        "user_id": user.id,
        "face_id": face_data.id,
        "enrollment_status": "REGISTERED",
        "face_registered": True
    }
