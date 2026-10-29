
import re

from sqlalchemy import create_engine, text, inspect

from database import (
    SERVER_URL, DB_NAME,
    Base, engine
)

# Import supaya seluruh tabel terdaftar
import models


def initialize_database():
    # Validasi nama database agar aman untuk SQL
    if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
        raise ValueError("Nama database tidak valid")

    # Membuat database jika belum ada
    server_engine = create_engine(SERVER_URL)

    with server_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4"
            )
        )
        conn.commit()

    server_engine.dispose()

    # Membuat tabel yang belum tersedia
    Base.metadata.create_all(bind=engine)

    print("Database berhasil disiapkan!")
    print("Nama database:", DB_NAME)

    print("\nDaftar tabel:")
    for table_name in inspect(engine).get_table_names():
        print("-", table_name)


if __name__ == "__main__":
    initialize_database()
