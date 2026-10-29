# 🚆 Smart Railway Boarding Gate (RailGate)

Sistem simulasi pemesanan tiket kereta api dan verifikasi gerbang boarding otomatis berbasis **Face Recognition** (Pengenalan Wajah). Proyek ini dibangun menggunakan **FastAPI** di sisi backend, database **MySQL** dengan **SQLAlchemy ORM**, serta antarmuka web modern bernuansa **Kereta Api Indonesia (KAI)**.

---

## 📌 Daftar Isi
- [Fitur Utama](#-fitur-utama)
- [Tech Stack](#-tech-stack)
- [Struktur Direktori](#-struktur-direktori)
- [Prasyarat Sistem](#-prasyarat-sistem)
- [Panduan Instalasi & Setup](#-panduan-instalasi--setup)
- [Konfigurasi Environment (.env)](#-konfigurasi-environment-env)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [Alur Pengujian Aplikasi](#-alur-pengujian-aplikasi)
- [Daftar Endpoint API](#-daftar-endpoint-api)

---

## ✨ Fitur Utama

1. **Autentikasi & Otorisasi Pengguna (JWT & Argon2)**:
   - Registrasi dan login penumpang dengan hashing password aman (`pwdlib` / Argon2).
   - Akses API dilindungi JSON Web Token (Bearer JWT).
   - Dukungan multi-role (`user` penumpang dan `admin` petugas gate).
2. **Face Enrollment (Pendaftaran Wajah)**:
   - Pengambilan/unggah foto wajah melalui kamera atau file gambar (JPG/PNG).
   - Validasi integritas gambar, batasan ukuran (maks. 5 MB), dan resolusi minimum (160x160 px).
   - Ekstraksi dan penyimpanan embedding wajah ke database MySQL melalui integrasi layanan AI.
3. **Pemesanan Tiket Kereta (Booking Ticket)**:
   - Pemilihan jadwal perjalanan kereta api yang aktif.
   - Pembuatan kode booking acak yang unik.
4. **Boarding Gate Verification & Face Scanner**:
   - Simulator verifikasi kamera boarding gate secara real-time.
   - Pengecekan status tiket (`BOOKED` → `BOARDED`) secara atomik.
   - Pengecekan jendela waktu boarding (dapat di-bypass saat mode pengujian dengan `SKIP_BOARDING_TIME_CHECK`).
   - Mode Mock Verification (`/dev-verify`) untuk mempermudah testing alur AI.
5. **Dashboard Admin & Riwayat Boarding**:
   - Dashboard monitoring status riwayat boarding gate (`GRANTED` / `DENIED`).
   - Logging detail pencocokan wajah: `similarity`, `scan_time`, dan alasan penolakan/penerimaan.
6. **Antarmuka Web Modern (KAI-Inspired RailGate)**:
   - Tampilan bersih, intuitif, dan responsif dengan palet warna khas KAI (Navy & Orange).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: MySQL / MariaDB, SQLAlchemy 2.0, PyMySQL
- **Keamanan & Kriptografi**: PyJWT, PwdLib (Argon2-cffi)
- **Image Processing & HTTP**: Pillow (PIL), HTTPX
- **Frontend**: HTML5, Vanilla JavaScript (Fetch API & SessionStorage), CSS3 (KAI Modern Theme)

---

## 📁 Struktur Direktori

```text
smart-boarding-gate/
├── backend/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Endpoint registrasi, login, & profil user
│   │   ├── boarding.py         # Endpoint boarding gate (dev-verify & logs)
│   │   ├── enrollment.py       # Endpoint pendaftaran wajah & simpan embedding
│   │   └── tickets.py          # Endpoint jadwal kereta & pemesanan tiket
│   ├── services/
│   │   ├── ai_client.py        # Client penghubung ke service AI Face Recognition
│   │   └── boarding_service.py # Logika validasi tiket & verifikasi boarding
│   ├── create_admin.py         # Script CLI untuk menetapkan role admin ke user
│   ├── database.py             # Konfigurasi koneksi MySQL & sesi SQLAlchemy
│   ├── init_db.py              # Script inisialisasi database dan pembuatan tabel
│   ├── main.py                 # File utama FastAPI server & router mounting
│   ├── models.py               # Model tabel SQLAlchemy (User, Ticket, Train, dll.)
│   ├── requirements.txt        # Daftar dependensi Python
│   ├── schemas.py              # Skema validasi Pydantic
│   └── security.py             # Enkripsi password & manajemen token JWT
├── frontend/
│   ├── css/
│   │   └── style.css           # Styling tampilan modern KAI RailGate
│   ├── js/
│   │   └── auth.js             # Helper JavaScript autentikasi & request API
│   ├── admin.html              # Dashboard admin untuk monitoring boarding log
│   ├── booking.html            # Halaman pemesanan tiket kereta
│   ├── dashboard.html          # Dashboard utama penumpang
│   ├── enrollment.html         # Halaman registrasi wajah penumpang
│   ├── index.html              # Landing page sistem Smart Boarding Gate
│   ├── login.html              # Halaman masuk akun
│   ├── my-tickets.html         # Halaman daftar e-ticket penumpang
│   ├── register.html           # Halaman pembuatan akun baru
│   └── scanner.html            # Antarmuka kamera scanner gerbang boarding
├── .env                        # Konfigurasi environment lokal (diabaikan git)
├── .env.example                # Template konfigurasi environment
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 💻 Prasyarat Sistem

Sebelum memulai, pastikan telah terpasang:
- **Python 3.10** atau lebih baru.
- **MySQL Server** (bisa menggunakan **XAMPP**, **Laragon**, **MySQL Community Server**, atau **Docker**).
- **Web Browser** modern (Google Chrome, Microsoft Edge, atau Mozilla Firefox) dengan izin akses webcam jika menguji scanner.

---

## 🚀 Panduan Instalasi & Setup

### 1. Masuk ke Direktori Proyek
Buka terminal / PowerShell dan arahkan ke folder proyek:
```bash
cd "smart-boarding-gate"
```

### 2. Buat dan Aktifkan Virtual Environment
```bash
# Membuat virtual environment
python -m venv backend/.venv

# Mengaktifkan di Windows (PowerShell)
.\backend\.venv\Scripts\Activate.ps1

# Atau Windows (CMD)
.\backend\.venv\Scripts\activate.bat

# Linux/macOS
source backend/.venv/bin/activate
```

### 3. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi File Environment (`.env`)
Salin file `.env.example` menjadi `.env`:
```bash
copy .env.example .env
```
Sesuaikan nilai konfigurasi di dalam file `.env` (lihat bagian penjelasan di bawah).

### 5. Inisialisasi Database
Pastikan layanan MySQL sudah berjalan (misalnya tombol **Start MySQL** pada XAMPP Control Panel), lalu jalankan:
```bash
python backend/init_db.py
```
*Script ini akan otomatis membuat database `smart_boarding` dan seluruh tabel yang dibutuhkan jika belum ada.*

---

## ⚙️ Konfigurasi Environment (`.env`)

Contoh isi konfigurasi `.env`:

```env
# Koneksi MySQL Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=smart_boarding

# Keamanan JWT
JWT_SECRET=rahasia_kunci_jwt_acak_yang_panjang_dan_aman_12345

# Flag Pengujian Boarding Gate
ENABLE_MOCK_BOARDING=true
SKIP_BOARDING_TIME_CHECK=true

# Integrasi AI Service Face Recognition
AI_SERVICE_URL=http://127.0.0.1:8001
AI_SERVICE_KEY=secret_key_internal_ai_service
```

| Variabel | Keterangan |
| :--- | :--- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Kredensial koneksi database MySQL. |
| `JWT_SECRET` | Kunci rahasia untuk menandatangani access token JWT. |
| `ENABLE_MOCK_BOARDING` | Bernilai `true` untuk mengaktifkan endpoint simulasi verifikasi AI `/api/boarding/dev-verify`. |
| `SKIP_BOARDING_TIME_CHECK` | Bernilai `true` agar verifikasi boarding dapat dilakukan kapan saja tanpa terhalang waktu keberangkatan kereta saat testing. |
| `AI_SERVICE_URL` & `AI_SERVICE_KEY` | URL dan kunci otentikasi layanan eksternal AI Face Recognition. |

---

## 🏃 Menjalankan Aplikasi

Jalankan server backend FastAPI menggunakan Uvicorn:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
*Atau masuk ke direktori `backend/` terlebih dahulu:*
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Setelah server aktif, buka browser dan akses antarmuka web di:
👉 **http://127.0.0.1:8000** atau **http://localhost:8000**

Dokumentasi interaktif API Swagger dapat diakses di:
👉 **http://127.0.0.1:8000/docs**

---

## 🧪 Alur Pengujian Aplikasi

1. **Registrasi Akun Baru**:
   - Buka `http://localhost:8000/register.html`.
   - Masukkan Nama, Email, dan Password, lalu klik **Daftar Akun**.
2. **Login Penumpang**:
   - Masuk melalui `http://localhost:8000/login.html` menggunakan email dan password yang telah didaftarkan.
   - Pengguna akan diarahkan ke Dashboard Penumpang.
3. **Face Enrollment (Daftarkan Wajah)**:
   - Pilih menu **Registrasi Wajah** (`/enrollment.html`).
   - Unggah atau ambil foto selfie wajah yang jelas (format JPG/PNG).
   - Klik **Daftarkan Wajah**. Token disimpan secara otomatis dari sesi login.
4. **Pesan Tiket Kereta (Booking)**:
   - Buka menu **Pesan Tiket** (`/booking.html`).
   - Pilih jadwal perjalanan kereta api yang diinginkan dan klik **Pesan Tiket**.
5. **Cek Tiket Saya**:
   - Buka menu **Tiket Saya** (`/my-tickets.html`).
   - Pastikan tiket yang baru dipesan muncul dengan status `BOOKED`.
6. **Membuat Akun Admin**:
   - Buka terminal dan jalankan:
     ```bash
     python backend/create_admin.py
     ```
   - Masukkan email akun yang ingin dijadikan admin, lalu ketik `y` untuk konfirmasi.
   - Login ulang dengan akun admin tersebut untuk membuka menu **Dashboard Admin** (`/admin.html`).
7. **Pengujian Boarding Scanner & Riwayat**:
   - Di dashboard admin, klik **Buka Boarding Scanner** (`/scanner.html`) untuk menyalakan kamera gerbang boarding.
   - Riwayat setiap proses pemindaian (diterima/ditolak beserta skor similarity) dapat dipantau di halaman `/admin.html`.

---

## 📡 Daftar Endpoint API

### 🔐 Autentikasi (`/api/auth`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Mendaftarkan akun penumpang baru | Publik |
| `POST` | `/api/auth/login` | Login menggunakan form OAuth2, menghasilkan JWT access token | Publik |
| `GET` | `/api/auth/me` | Mengambil data profil pengguna yang sedang login | Authenticated |

### 👤 Face Enrollment (`/api/face`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/face/enroll` | Mengunggah foto wajah dan menyimpan data embedding | Authenticated |

### 🎟️ Tiket & Perjalanan (`/api/tickets`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tickets/trains` | Mendapatkan daftar seluruh jadwal kereta api | Authenticated |
| `POST` | `/api/tickets/book` | Memesan tiket perjalanan kereta api | Authenticated |
| `GET` | `/api/tickets/my-tickets` | Mengambil daftar tiket yang dimiliki pengguna | Authenticated |

### 🚪 Boarding Verification & Logs (`/api/boarding`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/boarding/dev-verify` | Endpoint pengujian simulasi pencocokan wajah & tiket boarding | Admin |
| `GET` | `/api/boarding/logs` | Mengambil 100 riwayat transaksi pemindaian gerbang boarding terbaru | Admin |

---

## 👥 Pengembang
Proyek dikembangkan untuk kebutuhan praktikum mata kuliah **Machine Learning** - Sistem Smart Boarding Gate Berbasis Face Recognition.

