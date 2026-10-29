"""Masukkan jadwal dummy dari daftar pengguna ke tabel trains.
Jalankan dari folder backend: python seed_jadwal_kereta.py
"""
from datetime import datetime, timezone
from sqlalchemy import select
from database import SessionLocal
from models import Train

DATA = '''37F|ARGO PARAHYANGAN TAMBAHAN|GAMBIR|04:00
386|LOKAL BANDUNG RAYA|CICALENGKA|04:05
407|LOKAL BANDUNG RAYA|PADALARANG|04:30
396|LOKAL BANDUNG RAYA|CICALENGKA|04:35
19|ARGO PARAHYANGAN|GAMBIR|05:00
377|LOKAL BANDUNG RAYA|PADALARANG|05:50
408|LOKAL BANDUNG RAYA|CICALENGKA|06:00
387|LOKAL BANDUNG RAYA|PADALARANG|06:12
21|ARGO PARAHYANGAN|GAMBIR|06:30
397|LOKAL BANDUNG RAYA|PADALARANG|07:09
80|LODAYA PAGI|SOLOBALAPAN|07:20
378|LOKAL BANDUNG RAYA|CICALENGKA|07:32
31|ARGO PARAHYANGAN|GAMBIR|07:35
388|LOKAL BANDUNG RAYA|CICALENGKA|08:05
423|LOKAL CIBATU|PURWAKARTA|08:15
409|LOKAL BANDUNG RAYA|PADALARANG|08:18
6|ARGO WILIS|SURABAYA GUBENG|08:30
33|ARGO PARAHYANGAN|GAMBIR|08:35
398|LOKAL BANDUNG RAYA|CICALENGKA|09:05
93/92|CIREMAI EKSPRES|CIKAMPEK/CIREBON|09:55
379|LOKAL BANDUNG RAYA|PADALARANG|10:12
410|LOKAL BANDUNG RAYA|CICALENGKA|10:15
389|LOKAL BANDUNG RAYA|PADALARANG|10:37
35F|ARGO PARAHYANGAN TAMBAHAN|GAMBIR|11:00
399|LOKAL BANDUNG RAYA|PADALARANG|11:32
380|LOKAL BANDUNG RAYA|CICALENGKA|11:45
23|ARGO PARAHYANGAN|GAMBIR|11:50
411|LOKAL BANDUNG RAYA|PADALARANG|12:32
390|LOKAL BANDUNG RAYA|CICALENGKA|12:40
400|LOKAL BANDUNG RAYA|CICALENGKA|13:20
381|LOKAL BANDUNG RAYA|PADALARANG|13:59
412|LOKAL BANDUNG RAYA|CICALENGKA|14:10
25|ARGO PARAHYANGAN|GAMBIR|14:30
391|LOKAL BANDUNG RAYA|PADALARANG|15:04
382|LOKAL BANDUNG RAYA|CICALENGKA|15:35
132|MUTIARA SELATAN|SURABAYA GUBENG|15:45
401|LOKAL BANDUNG RAYA|PADALARANG|15:51
27|ARGO PARAHYANGAN|GAMBIR|16:15
413|LOKAL BANDUNG RAYA|PADALARANG|16:42
100|MALABAR EKSPRES|MALANG|16:50
424|LOKAL CIBATU|CIBATU|17:00
392|LOKAL BANDUNG RAYA|CICALENGKA|17:02
402|LOKAL BANDUNG RAYA|CICALENGKA|17:40
414|LOKAL BANDUNG RAYA|CICALENGKA|18:20
383|LOKAL BANDUNG RAYA|PADALARANG|18:34
82|LODAYA MALAM|SOLOBALAPAN|18:55
29|ARGO PARAHYANGAN|GAMBIR|19:25
50|TURANGGA|SURABAYA GUBENG|19:30
97/96|CIREMAI EKSPRES|CIKAMPEK/CIREBON|19:45
393|LOKAL BANDUNG RAYA|PADALARANG|20:04
384|LOKAL BANDUNG RAYA|CICALENGKA|20:10
403|LOKAL BANDUNG RAYA|PADALARANG|20:32
415|LOKAL BANDUNG RAYA|PADALARANG|21:05
75/74|HARINA|CIKAMPEK/SURABAYA PASARTURI|21:25
394|LOKAL BANDUNG RAYA|CICALENGKA|21:43
404|LOKAL BANDUNG RAYA|CICALENGKA|22:08'''


def main():
    raw_date = input('Tanggal keberangkatan (YYYY-MM-DD): ').strip()
    try:
        departure_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
    except ValueError:
        print('Tanggal tidak valid. Contoh: 2026-10-29')
        return

    asal = input('Stasiun asal [BANDUNG]: ').strip().upper() or 'BANDUNG'
    records = []
    for line in DATA.splitlines():
        no_ka, nama, tujuan, waktu = line.split('|')
        dt_local = datetime.strptime(f'{departure_date.isoformat()} {waktu}', '%Y-%m-%d %H:%M')
        # Sistem lama menyimpan departure_time sebagai naive UTC.
        # Asumsikan jam jadwal dalam WIB (UTC+7), konversi ke UTC tanpa tzinfo.
        from datetime import timedelta
        dt_utc = dt_local - timedelta(hours=7)
        records.append((f'{no_ka} - {nama}', asal, tujuan, dt_utc))

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for nama, asal, tujuan, departure_time in records:
            existing = db.scalar(select(Train.id).where(
                Train.nama_kereta == nama,
                Train.asal == asal,
                Train.tujuan == tujuan,
                Train.departure_time == departure_time,
            ))
            if existing is not None:
                skipped += 1
                continue
            db.add(Train(nama_kereta=nama, asal=asal, tujuan=tujuan, departure_time=departure_time))
            inserted += 1
        db.commit()
        print(f'Berhasil: {inserted} jadwal baru, {skipped} dilewati karena duplikat.')
        print('Jam input dianggap WIB dan disimpan sebagai UTC, mengikuti utc_now() backend.')
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
