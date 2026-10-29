from datetime import datetime
from pathlib import Path

from routes.boarding import router as boarding_router
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import get_db
from models import Train
from routes.auth import router as auth_router
from routes.enrollment import router as enrollment_router
from routes.tickets import router as tickets_router

PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="Smart Boarding Gate API")


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend"
)

@app.get("/")
def home_page():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/{page_name}.html")
def html_page(page_name: str):
    allowed_pages = {
        "register", "login", "dashboard",
        "enrollment", "booking",
        "my-tickets", "admin", "scanner"
    }

    if page_name not in allowed_pages:
        raise HTTPException(
            status_code=404,
            detail="Halaman tidak ditemukan"
        )

    return FileResponse(
        FRONTEND_DIR / f"{page_name}.html"
    )

app.include_router(auth_router)
app.include_router(enrollment_router)
app.include_router(tickets_router)
app.include_router(boarding_router)

class TrainCreate(BaseModel):
    nama_kereta: str
    asal: str
    tujuan: str
    departure_time: datetime


@app.get("/")
def home():
    return {
        "message": "Smart Boarding Gate Running"
    }


@app.get("/enrollment")
def enrollment_page():
    return FileResponse(
        PROJECT_ROOT / "frontend" / "enrollment.html"
    )


@app.get("/api/database/check")
def check_database(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "message": "MySQL berhasil terhubung"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Koneksi MySQL gagal"
        )


@app.get("/api/trains")
def lihat_kereta(db: Session = Depends(get_db)):

    semua_kereta = (
        db.query(Train)
        .order_by(Train.id)
        .all()
    )

    return [
        {
            "id": kereta.id,
            "nama_kereta": kereta.nama_kereta,
            "asal": kereta.asal,
            "tujuan": kereta.tujuan,
            "departure_time": kereta.departure_time
        }
        for kereta in semua_kereta
    ]

