import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(
    Path(__file__).resolve().parents[2] / ".env",
    override=True
)

SKIP_BOARDING_TIME_CHECK = (
    os.getenv("SKIP_BOARDING_TIME_CHECK", "false").lower()
    == "true"
)

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models import User, Train, Ticket, BoardingLog


def utc_now():
    return datetime.now(timezone.utc).replace(
        tzinfo=None
    )


def verify_boarding(
    db: Session,
    user_id: int | None,
    train_id: int,
    matched: bool,
    similarity: float | None = None
):
    now = utc_now()
    ticket = None
    result = "DENIED"
    reason = ""

    try:
        train = db.get(Train, train_id)

        if not matched or user_id is None:
            reason = "Wajah tidak dikenali"
            user_id = None

        elif db.get(User, user_id) is None:
            reason = "User tidak terdaftar"
            user_id = None

        elif train is None:
            reason = "Perjalanan tidak ditemukan"

        else:
            ticket = db.scalar(
                select(Ticket)
                .where(
                    Ticket.user_id == user_id,
                    Ticket.train_id == train_id
                )
            )

            if ticket is None:
                reason = "Tiket tidak ditemukan"

            elif ticket.status == "BOARDED":
                reason = "Tiket sudah digunakan"

            elif ticket.status != "BOOKED":
                reason = "Tiket tidak aktif"

            elif (
                not SKIP_BOARDING_TIME_CHECK
                and not (
                    train.departure_time - timedelta(minutes=90)
                    <= now
                    <= train.departure_time + timedelta(minutes=15)
                )
            ):
                reason = "Di luar waktu boarding"


            else:
                # Atomic update mencegah satu tiket
                # dipakai dua kali secara bersamaan.
                statement = (
                    update(Ticket)
                    .where(
                        Ticket.id == ticket.id,
                        Ticket.status == "BOOKED"
                    )
                    .values(
                        status="BOARDED",
                        boarded_at=now
                    )
                )

                changed = db.execute(statement)

                if changed.rowcount == 1:
                    result = "GRANTED"
                    reason = "Boarding berhasil"
                else:
                    reason = "Tiket sudah digunakan"

        log = BoardingLog(
            user_id=user_id,
            ticket_id=ticket.id if ticket else None,
            scan_time=now,
            similarity=similarity,
            result=result,
            reason=reason
        )

        db.add(log)
        db.commit()

        return {
            "boarding_status": result,
            "user_id": user_id,
            "ticket_id": ticket.id if ticket else None,
            "message": reason
        }

    except Exception:
        db.rollback()
        raise
