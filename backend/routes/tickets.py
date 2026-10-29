
import secrets
from datetime import datetime, timezone

from fastapi import (
    APIRouter, Depends, HTTPException
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User, Train, Ticket
from security import get_current_user

router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"]
)


class BookingRequest(BaseModel):
    train_id: int


def ticket_response(ticket, train):
    return {
        "ticket_id": ticket.id,
        "train_id": train.id,
        "booking_code": ticket.booking_code,
        "nama_kereta": train.nama_kereta,
        "asal": train.asal,
        "tujuan": train.tujuan,
        "departure_time": train.departure_time,
        "status": ticket.status
    }


# MELIHAT PERJALANAN TERSEDIA
@router.get("/trains")
def available_trains(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    trains = db.scalars(
        select(Train)
        .where(Train.departure_time > now)
        .order_by(Train.departure_time)
    ).all()

    return [
        {
            "id": train.id,
            "nama_kereta": train.nama_kereta,
            "asal": train.asal,
            "tujuan": train.tujuan,
            "departure_time": train.departure_time
        }
        for train in trains
    ]


# BOOKING TIKET DUMMY
@router.post("/book", status_code=201)
def book_ticket(
    data: BookingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    train = db.get(Train, data.train_id)

    if train is None:
        raise HTTPException(
            status_code=404,
            detail="Jadwal kereta tidak ditemukan"
        )

    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    if train.departure_time <= now:
        raise HTTPException(
            status_code=400,
            detail="Jadwal sudah lewat"
        )

    existing = db.scalar(
        select(Ticket).where(
            Ticket.user_id == user.id,
            Ticket.train_id == train.id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Anda sudah memiliki tiket ini"
        )

    ticket = Ticket(
        user_id=user.id,
        train_id=train.id,
        booking_code="SIM-" + secrets.token_hex(8).upper(),
        status="BOOKED"
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Booking gagal karena data duplikat"
        )

    return {
        "message": "Pemesanan tiket berhasil",
        **ticket_response(ticket, train)
    }


# MELIHAT TIKET MILIK SENDIRI
@router.get("/my-tickets")
def my_tickets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    results = db.execute(
        select(Ticket, Train)
        .join(Train, Ticket.train_id == Train.id)
        .where(Ticket.user_id == user.id)
        .order_by(Ticket.id.desc())
    ).all()

    return [
        ticket_response(ticket, train)
        for ticket, train in results
    ]
