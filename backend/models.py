
from datetime import datetime, timezone

from sqlalchemy import (
    Integer, String, ForeignKey,
    DateTime, LargeBinary, Float, Text,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def waktu_sekarang():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# 1. TABEL USERS
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nama: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(
        String(150), unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20), default="user"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=waktu_sekarang
    )


# 2. TABEL FACE EMBEDDINGS
class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    embedding: Mapped[bytes] = mapped_column(LargeBinary)
    model_version: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=waktu_sekarang
    )


# 3. TABEL TRAINS
class Train(Base):
    __tablename__ = "trains"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nama_kereta: Mapped[str] = mapped_column(String(100))
    asal: Mapped[str] = mapped_column(String(100))
    tujuan: Mapped[str] = mapped_column(String(100))
    departure_time: Mapped[datetime] = mapped_column(DateTime)


# 4. TABEL TICKETS
class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "train_id",
            name="uq_user_train"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    train_id: Mapped[int] = mapped_column(
        ForeignKey("trains.id"), index=True
    )
    booking_code: Mapped[str] = mapped_column(
        String(50), unique=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="BOOKED"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=waktu_sekarang
    )
    boarded_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


# 5. TABEL BOARDING LOGS
class BoardingLog(Base):
    __tablename__ = "boarding_logs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id"), nullable=True
    )
    scan_time: Mapped[datetime] = mapped_column(
        DateTime, default=waktu_sekarang
    )
    similarity: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    result: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
