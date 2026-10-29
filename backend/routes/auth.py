
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User, Ticket, FaceEmbedding, BoardingLog
from schemas import UserRegister, UserResponse, TokenResponse
from security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# 1. REGISTRASI USER
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db)
):

    email = str(data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email sudah terdaftar"
        )

    user = User(
        nama=data.nama.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role="user"
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email sudah terdaftar"
        )

    return user


# 2. LOGIN USER
@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    email = form.username.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        form.password, user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Email atau password salah"
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# 3. PROFIL USER YANG LOGIN
@router.get(
    "/me",
    response_model=UserResponse
)
def my_profile(
    user: User = Depends(get_current_user)
):
    return user


# 4. ENDPOINT KHUSUS ADMIN
@router.get("/admin/check")
def admin_check(
    admin: User = Depends(require_admin)
):
    return {
        "message": "Akses admin berhasil",
        "nama": admin.nama,
        "role": admin.role
    }


# 5. DAFTAR SEMUA PENGGUNA (KHUSUS ADMIN)
@router.get("/admin/users")
def list_admin_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    users = db.scalars(
        select(User).order_by(User.id.desc())
    ).all()

    face_user_ids = set(
        db.scalars(select(FaceEmbedding.user_id)).all()
    )

    return [
        {
            "id": u.id,
            "nama": u.nama,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at,
            "has_face": u.id in face_user_ids
        }
        for u in users
    ]


# 6. HAPUS AKUN PENGGUNA (KHUSUS ADMIN)
@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Akun pengguna tidak ditemukan"
        )

    if target.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Akun admin lain tidak dapat dihapus"
        )

    try:
        # Riwayat boarding milik akun target.
        db.execute(
            delete(BoardingLog).where(
                BoardingLog.user_id == user_id
            )
        )
        # Pertahankan log yang mungkin mereferensikan
        # tiket user tetapi user_id log-nya kosong.
        ticket_ids = select(Ticket.id).where(
            Ticket.user_id == user_id
        )
        db.execute(
            delete(BoardingLog).where(
                BoardingLog.ticket_id.in_(ticket_ids)
            )
        )
        # Hapus tiket dan embedding milik pengguna.
        db.execute(
            delete(Ticket).where(Ticket.user_id == user_id)
        )
        db.execute(
            delete(FaceEmbedding).where(
                FaceEmbedding.user_id == user_id
            )
        )
        # Hapus akun terakhir.
        db.delete(target)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Gagal menghapus akun. Periksa relasi database."
        )

    return {
        "message": "Akun dan data terkait berhasil dihapus",
        "deleted_user_id": user_id
    }


