
from sqlalchemy import select

from database import SessionLocal
from models import User


def create_admin():
    email = input("Email akun yang akan dijadikan admin: ")
    email = email.strip().lower()

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if not user:
            print("Akun tidak ditemukan!")
            return

        if user.role == "admin":
            print("Akun sudah menjadi admin.")
            return

        konfirmasi = input(
            f"Jadikan {user.nama} sebagai admin? (y/n): "
        )

        if konfirmasi.lower() != "y":
            print("Dibatalkan.")
            return

        user.role = "admin"
        db.commit()

        print(f"Berhasil! {user.nama} sekarang admin.")


if __name__ == "__main__":
    create_admin()
