# 🚆 RailGate — Smart Railway Boarding Gate System
### Sistem Simulasi Pemesanan Tiket & Verifikasi Boarding Gate Berbasis Face Recognition (KAI Style)

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1.svg)](https://www.mysql.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Face_Detection-00FFFF.svg)](https://github.com/akanametov/yolo-face)
[![InsightFace](https://img.shields.io/badge/InsightFace-ArcFace_buffalo__l-orange.svg)](https://github.com/deepinsight/insightface)
[![Theme](https://img.shields.io/badge/UI%20Theme-KAI%20Modern%20Navy%20%26%20Orange-EC6608.svg)](#)

---

## 📌 Daftar Isi
- [Tentang Proyek](#-tentang-proyek)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Fitur Utama](#-fitur-utama)
- [Tech Stack](#-tech-stack)
- [Struktur Direktori](#-struktur-direktori)
- [Prasyarat Sistem](#-prasyarat-sistem)
- [Panduan Instalasi & Setup](#-panduan-instalasi--setup)
  - [1. Clone Repository & Setup Virtual Environment](#1-clone-repository--setup-virtual-environment)
  - [2. Setup Layanan AI (ai_service)](#2-setup-layanan-ai-ai_service)
  - [3. Setup Backend & Database MySQL](#3-setup-backend--database-mysql)
  - [4. Konfigurasi File Environment (.env)](#4-konfigurasi-file-environment-env)
  - [5. Inisialisasi Database & Seeding Jadwal](#5-inisialisasi-database--seeding-jadwal)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [Alur Pengujian Aplikasi Lengkap](#-alur-pengujian-aplikasi-lengkap)
- [Dokumentasi API Endpoint](#-dokumentasi-api-endpoint)
  - [Backend Endpoints (Port 8000)](#backend-endpoints-port-8000)
  - [AI Service Endpoints (Port 8001 - Internal)](#ai-service-endpoints-port-8001---internal)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Pengembang](#-pengembang)

---

## 📖 Tentang Proyek

**RailGate (Smart Railway Boarding Gate)** adalah solusi simulasi gerbang boarding otomatis berbasis kecerdasan buatan (*Computer Vision & Deep Learning*) yang terinspirasi oleh sistem Face Recognition Boarding Gate milik **PT Kereta Api Indonesia (KAI)**.

Sistem ini memfasilitasi proses *seamless boarding* tanpa tiket fisik:
1. Penumpang mendaftarkan akun dan mendaftarkan wajah (*Face Enrollment*).
2. Penumpang memesan tiket kereta api (*Booking Ticket*).
3. Di gerbang boarding, kamera pemindai (*Webcam Scanner*) menangkap wajah penumpang secara *real-time*.
4. Sistem AI mendeteksi wajah dengan **YOLOv8-Face**, mengekstrak fitur 512 dimensi menggunakan **ArcFace (InsightFace `buffalo_l`)**, dan mencocokkan kemiripan (*Cosine Similarity*) terhadap galeri database.
5. Backend memvalidasi tiket secara atomik: jadwal kereta, jendela waktu boarding, dan kepemilikan tiket sebelum membuka gerbang (`GRANTED` / `DENIED`).

---

## 🏗️ Arsitektur Sistem

Sistem ini dirancang menggunakan arsitektur modular terpisah (*Microservice-ready*) antara logika bisnis dan komputasi model AI:

```mermaid
graph TD
    subgraph Klien / Frontend (Port 8000)
        UI[Web UI KAI Style HTML/CSS/JS]
        Cam[Kamera Webcam Boarding Scanner]
    end

    subgraph Backend Utama (Port 8000 - FastAPI)
        API[FastAPI Main Server]
        AuthSvc[Auth & JWT Service]
        BoardingSvc[Boarding Validation Logic]
        AIClient[Internal AI HTTP Client]
    end

    subgraph Database
        DB[(MySQL Database)]
        T_Users[Tabel Users]
        T_Trains[Tabel Trains]
        T_Tickets[Tabel Tickets]
        T_Faces[Tabel Face Embeddings 512-dim]
        T_Logs[Tabel Boarding Logs]
    end

    subgraph AI Service (Port 8001 - FastAPI)
        AIEngine[AI Engine API]
        YOLO[YOLOv8-Face Detector]
        ArcFace[InsightFace ArcFace buffalo_l]
        Matcher[Cosine Similarity Matcher]
    end

    UI -->|HTTP / JSON| API
    Cam -->|Frame Image / Multipart| API
    API --> AuthSvc
    API --> BoardingSvc
    BoardingSvc --> DB
    BoardingSvc --> AIClient
    AIClient -->|HTTP X-AI-Key: /ai/embed & /ai/match| AIEngine
    AIEngine --> YOLO
    YOLO --> ArcFace
    ArcFace --> Matcher
```

---

## ✨ Fitur Utama

### 1. 🔐 Autentikasi & Multi-Role User (JWT & Argon2)
- Registrasi dan login penumpang dengan password hashing berstandar industri (**Argon2** via `pwdlib`).
- Proteksi endpoint menggunakan **OAuth2 Password Bearer** & token **JWT (JSON Web Token)**.
- Dukungan peran ganda: role `user` (penumpang) dan `admin` (petugas stasiun/gate).
- Script CLI `backend/create_admin.py` untuk pembuatan dan promosi role admin.

### 2. 👤 Face Enrollment (Pendaftaran Wajah)
- Pengambilan foto wajah langsung melalui webcam atau unggah file foto (JPG/PNG).
- Validasi ketat pada backend: batas ukuran file (maksimal 5 MB), resolusi minimal (160x160 px), integritas citra (PIL).
- Ekstraksi vektor fitur wajah 512-dimensi oleh AI Service dan penyimpanan aman dalam format *binary BLOB* di database MySQL.
- Pencegahan pendaftaran ganda per akun pengguna.

### 3. 🎫 Manajemen & Pemesanan Tiket (Booking)
- Tampilan daftar jadwal perjalanan kereta api aktif yang siap dipesan.
- Pembuatan kode booking unik otomatis berformat `SIM-XXXXXXXX`.
- Pengecekan tiket ganda untuk jadwal keberangkatan yang sama.
- Halaman **Tiket Saya** untuk melihat seluruh e-ticket dan statusnya (`BOOKED` atau `BOARDED`).

### 4. 📷 Boarding Scanner Real-Time
- Antarmuka pemindai gerbang boarding interaktif dengan pemilihan jadwal kereta aktif.
- Penangkapan frame kamera otomatis dan pengiriman langsung ke backend via `/api/boarding/scan`.
- AI mengenali identitas penumpang tanpa input manual identitas, kemudian memvalidasi:
  - Apakah wajah terdeteksi dan cocok dengan akun di database?
  - Apakah skor kemiripan (*similarity*) melampaui ambang batas (*threshold* $\ge 0.50$)?
  - Apakah penumpang memiliki tiket sah untuk kereta tersebut?
  - Apakah status tiket masih `BOOKED` dan belum pernah digunakan?
  - Apakah waktu keberangkatan berada dalam jendela boarding yang valid?
- Gerbang memberikan respon visual instan (*GRANTED* hijau / *DENIED* merah) disertai nama penumpang dan kode booking.

### 5. 📊 Dashboard Admin & Manajemen Pengguna
- **Boarding Logs Real-Time**: Riwayat 100 aktivitas boarding terakhir dengan rincian nama penumpang, nomor tiket, timestamp, status (`GRANTED`/`DENIED`), skor kemiripan, dan alasan penolakan.
- **Manajemen Akun Penumpang**: Melihat seluruh pengguna terdaftar, status registrasi wajah (*Face Enrolled*), dan opsi hapus akun secara kaskad (*cascade cleanup*).
- **Mode Simulasi Pengujian**: Endpoint `/api/boarding/dev-verify` untuk pengujian tanpa kamera.

### 6. 🎨 Antarmuka KAI Modern & Responsif
- Desain antarmuka terinspirasi dari aplikasi resmi KAI Access / Access by KAI dengan palet warna khas: **Navy (`#002B66`)** dan **Orange (`#ED6B28`)**.
- Notifikasi interaktif dan dialog konfirmasi modern berbasis SweetAlert2.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: MySQL 8.0+, SQLAlchemy 2.0, PyMySQL, Cryptography
- **Keamanan**: PyJWT, PwdLib (Argon2-cffi)
- **Komunikasi & Citra**: HTTPX (Asynchronous HTTP), Pillow (PIL)

### AI Service (Engine Face Recognition)
- **Framework**: FastAPI, Uvicorn
- **Deteksi Wajah**: YOLOv8-Face (`yolov8n-face.pt`) via Ultralytics
- **Ekstraksi Fitur / Embedding**: InsightFace (`buffalo_l`), ONNX Runtime, OpenCV (cv2), NumPy
- **Metrik Pencocokan**: Cosine Similarity & Vector Norm L2

### Frontend
- **Arsitektur**: Vanilla HTML5, CSS3 Modern (KAI Design System), JavaScript (ES6+ Fetch API & SessionStorage)
- **Libraries**: SweetAlert2, MediaDevices (WebRTC Webcam API)

---

## 📁 Struktur Direktori

```text
KAI-access/
├── ai_service/                     # Layanan Mandiri AI Face Recognition (Port 8001)
│   ├── dataset/                    # Sampel dataset pendaftaran & validasi
│   ├── docs/                       # Dokumentasi kontrak API internal (CONTRACT.md)
│   ├── models/                     # Tempat bobot model YOLOv8 (yolov8n-face.pt)
│   ├── scripts/                    # Script CLI testing kamera, batch, & evaluasi
│   │   ├── boarding_scanner.py     # Scanner mandiri berbasis OpenCV
│   │   ├── camera_demo.py          # Demo pengujian webcam lokal
│   │   └── local_enroll.py         # Script enrollment galeri lokal
│   ├── src/                        # Source code mesin AI
│   │   ├── api.py                  # Server FastAPI internal endpoint (/ai/embed, /ai/match)
│   │   └── face_engine.py          # Pipeline deteksi YOLO + embedding ArcFace
│   ├── tests/                      # Unit test pencocokan embedding
│   ├── .env.example                # Template konfigurasi environment AI service
│   ├── requirements.txt            # Dependensi library AI (Ultralytics, InsightFace, dll.)
│   └── README.md                   # Panduan teknis khusus AI Service
│
├── backend/                        # Backend Utama Sistem RailGate (Port 8000)
│   ├── routes/
│   │   ├── auth.py                 # Endpoint login, registrasi, profil, & manajemen admin
│   │   ├── boarding.py             # Endpoint verifikasi scanner (/scan) & boarding logs
│   │   ├── enrollment.py           # Endpoint pendaftaran wajah penumpang (/enroll)
│   │   └── tickets.py              # Endpoint jadwal perjalanan & pemesanan tiket
│   ├── services/
│   │   ├── ai_client.py            # HTTP Client pengirim frame/vektor ke ai_service
│   │   └── boarding_service.py     # Logika bisnis validasi tiket & verifikasi boarding
│   ├── create_admin.py             # Script CLI promosi role admin
│   ├── database.py                 # Konfigurasi koneksi MySQL & sesi SQLAlchemy
│   ├── init_db.py                  # Script pembuatan database & tabel otomatis
│   ├── main.py                     # Entry point FastAPI server & static file mounting
│   ├── models.py                   # Definisi model relasional database (SQLAlchemy)
│   ├── requirements.txt            # Dependensi backend
│   ├── schemas.py                  # Skema validasi request & response (Pydantic)
│   ├── security.py                 # Logika hashing Argon2, JWT token, & dependency injection
│   └── seed_jadwal_kereta.py       # Script CLI seeding jadwal kereta realistis
│
├── frontend/                       # Antarmuka Pengguna Web (KAI Theme)
│   ├── css/
│   │   └── style.css               # Desain UI modern KAI (Navy & Orange)
│   ├── js/
│   │   ├── app.js                  # Logika aplikasi umum
│   │   └── auth.js                 # Helper token JWT, status login, & request handler
│   ├── admin.html                  # Dashboard admin & pemantauan log gate
│   ├── booking.html                # Halaman pemesanan tiket kereta
│   ├── dashboard.html              # Halaman beranda penumpang setelah login
│   ├── enrollment.html             # Halaman registrasi wajah pengguna
│   ├── index.html                  # Landing page utama RailGate
│   ├── login.html                  # Halaman masuk akun
│   ├── my-tickets.html             # Halaman daftar tiket yang dimiliki
│   ├── register.html               # Halaman pendaftaran akun baru
│   └── scanner.html                # Antarmuka live camera scanner gerbang boarding
│
├── .env.example                    # Template environment backend utama
├── .gitignore
├── README.md                       # Dokumentasi utama proyek
└── requirements.txt                # Dependensi gabungan backend
```

---

## 💻 Prasyarat Sistem

Sebelum melakukan instalasi, pastikan lingkungan komputer telah memenuhi:
1. **Sistem Operasi**: Windows 10/11, Linux (Ubuntu 20.04+), atau macOS.
2. **Python**: Versi **3.10** atau **3.11** (64-bit disarankan untuk kompatibilitas InsightFace & ONNX Runtime).
3. **Database Server**: **MySQL 8.0+** atau MariaDB (dapat menggunakan **XAMPP**, **Laragon**, atau MySQL Community Server).
4. **Kamera / Webcam**: Diperlukan untuk pengujian pendaftaran wajah dan scanner boarding.
5. **Koneksi Internet**: Untuk download awal bobot model ArcFace `buffalo_l` (~326 MB) dan YOLOv8-face (~6 MB).

---

## 🚀 Panduan Instalasi & Setup

Ikuti langkah-langkah berikut secara berurutan untuk memasang dan menjalankan sistem.

### 1. Clone Repository & Setup Virtual Environment

Buka terminal (PowerShell atau Command Prompt) lalu arahkan ke direktori proyek:

```bash
# Clone repository jika belum
git clone https://github.com/barravasska/KAI-access.git
cd KAI-access
```

Buat dan aktifkan virtual environment Python:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv .venv
.\.venv\Scripts\activate.bat

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

> **Tips PowerShell**: Jika muncul pesan error *ExecutionPolicy*, jalankan perintah:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` lalu ulangi pengaktifan venv.

---

### 2. Setup Layanan AI (`ai_service`)

Layanan AI memerlukan instalasi dependensi *computer vision* dan bobot model deteksi wajah.

1. **Instal dependensi AI Service**:
   ```bash
   pip install -r ai_service/requirements.txt
   ```

2. **Download Bobot Model YOLOv8-Face**:
   Pastikan folder `ai_service/models/` tersedia, lalu unduh bobot `yolov8n-face.pt`:
   ```powershell
   # Melalui PowerShell:
   Invoke-WebRequest -Uri "https://huggingface.co/junjiang/GestureFace/resolve/main/yolov8n-face.pt" -OutFile "ai_service/models/yolov8n-face.pt"
   ```
   *(Alternatif: Unduh manual dari [HuggingFace junjiang/GestureFace](https://huggingface.co/junjiang/GestureFace/resolve/main/yolov8n-face.pt) dan simpan di folder `ai_service/models/yolov8n-face.pt`).*

3. **Konfigurasi Environment AI Service**:
   Salin file konfigurasi di folder `ai_service`:
   ```bash
   copy ai_service\.env.example ai_service\.env
   ```
   Buka file `ai_service/.env` dan pastikan konfigurasi sesuai:
   ```env
   AI_API_KEY=kunci_rahasia_internal_ai_railgate_12345
   YOLO_WEIGHTS=models/yolov8n-face.pt
   ARCFACE_PACK=buffalo_l
   MATCH_THRESHOLD=0.50
   MATCH_MARGIN=0.04
   MIN_FACE_SIZE=90
   BLUR_THRESHOLD=55
   ```
   *(Catatan: Bobot ArcFace `buffalo_l` akan diunduh secara otomatis oleh InsightFace ke folder cache user saat pertama kali service dijalankan).*

---

### 3. Setup Backend & Database MySQL

1. **Instal dependensi Backend**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Pastikan Layanan MySQL Aktif**:
   - Jika menggunakan **XAMPP**, buka XAMPP Control Panel dan klik tombol **Start** pada modul **MySQL**.
   - Jika menggunakan **Laragon**, pastikan layanan MySQL berstatus *Running*.

---

### 4. Konfigurasi File Environment (`.env`)

Salin file `.env.example` di root proyek menjadi `.env`:

```bash
copy .env.example .env
```

Buka dan sesuaikan isi file `.env` pada root:

```env
# Koneksi Database MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=smart_boarding

# Kunci Rahasia JWT Token
JWT_SECRET=super_secret_jwt_key_kai_railgate_development_random_hash_98765

# Integrasi ke AI Service (Harus cocok dengan AI_API_KEY di ai_service/.env)
AI_SERVICE_URL=http://127.0.0.1:8001
AI_SERVICE_KEY=kunci_rahasia_internal_ai_railgate_12345

# Flag Pengujian
ENABLE_MOCK_BOARDING=true
SKIP_BOARDING_TIME_CHECK=true
```

> [!IMPORTANT]
> Pastikan nilai `AI_SERVICE_KEY` pada file `.env` root **sama persis** dengan `AI_API_KEY` pada file `ai_service/.env`.

---

### 5. Inisialisasi Database & Seeding Jadwal

Jalankan script untuk membuat database `smart_boarding` dan seluruh tabel:

```bash
python backend/init_db.py
```
*Output akan menampilkan nama database dan tabel yang berhasil dibuat: `users`, `trains`, `tickets`, `face_embeddings`, dan `boarding_logs`.*

Selanjutnya, isi data dummy jadwal kereta api:

```bash
python backend/seed_jadwal_kereta.py
```
*Masukkan tanggal keberangkatan saat diminta (format: `YYYY-MM-DD`, contoh tanggal hari ini atau beberapa hari ke depan) dan stasiun asal (default: `BANDUNG`). Puluhan jadwal kereta seperti Argo Parahyangan, Lodaya, Turangga, dll. akan otomatis dimasukkan ke database.*

---

## 🏃 Menjalankan Aplikasi

Sistem memerlukan **2 terminal aktif**: satu untuk **AI Service (Port 8001)** dan satu untuk **Backend FastAPI (Port 8000)**.

### Terminal 1: Jalankan AI Service
```powershell
# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Pindah ke direktori ai_service dan jalankan server
cd ai_service
uvicorn src.api:app --host 127.0.0.1 --port 8001 --reload
```
Layanan AI akan aktif di 👉 **http://127.0.0.1:8001** (Dokumentasi internal: `/docs`).

---

### Terminal 2: Jalankan Backend & Web UI
Buka terminal baru di root proyek `KAI-access`:
```powershell
# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Jalankan server utama FastAPI
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Aplikasi web utama aktif di 👉 **http://127.0.0.1:8000** (Dokumentasi API Swagger: `/docs`).

---

## 🧪 Alur Pengujian Aplikasi Lengkap

Berikut alur lengkap pengujian skenario *end-to-end* sistem RailGate:

### Skenario 1: Registrasi & Pendaftaran Wajah Penumpang
1. Buka browser ke **http://localhost:8000**.
2. Klik tombol **Daftar Akun** (`/register.html`).
3. Masukkan Nama, Email, dan Password (misal: `penumpang@kai.id`), lalu klik **Daftar Akun**.
4. Login menggunakan akun tersebut di `/login.html`. Anda akan diarahkan ke **Dashboard Penumpang** (`/dashboard.html`).
5. Klik menu **Registrasi Wajah** (`/enrollment.html`).
6. Nyalakan kamera webcam dan ambil foto (*Capture Face*) atau unggah foto selfie yang jelas.
7. Klik **Daftarkan Wajah**.
   - Sistem akan mengirimkan foto ke AI Service untuk diekstraksi menjadi embedding 512-dimensi.
   - Embedding berhasil disimpan ke tabel `face_embeddings` di database.

### Skenario 2: Pemesanan Tiket Kereta (Booking)
1. Pada menu dashboard penumpang, pilih **Pesan Tiket** (`/booking.html`).
2. Pilih salah satu perjalanan kereta yang tersedia (misalnya: *Argo Parahyangan* rute Bandung - Gambir).
3. Klik **Pesan Tiket**.
4. Buka menu **Tiket Saya** (`/my-tickets.html`) untuk melihat e-ticket Anda yang kini berstatus **`BOOKED`** beserta kode booking unik.

### Skenario 3: Pembuatan Akun Petugas / Admin
1. Buka terminal baru dan jalankan script admin:
   ```bash
   python backend/create_admin.py
   ```
2. Masukkan email yang telah didaftarkan (atau akun baru) untuk dipromosikan menjadi admin, ketik `y` untuk konfirmasi.
3. Login ulang menggunakan akun admin tersebut. Anda akan melihat menu khusus **Dashboard Admin** (`/admin.html`).

### Skenario 4: Boarding Gate Verification (Scanner Kamera)
1. Masuk ke halaman **Dashboard Admin** (`/admin.html`).
2. Klik tombol **Buka Boarding Scanner** (`/scanner.html`).
3. Pilih jadwal kereta api yang sesuai dengan tiket penumpang yang dipesan.
4. Klik **Mulai Kamera Scanner**. Arahkan wajah penumpang yang sudah terdaftar ke webcam:
   - Scanner mengambil frame dan memanggil endpoint `/api/boarding/scan`.
   - AI mengenali wajah, menghitung kemiripan (*similarity*), dan mencocokkan tiket penumpang di database.
   - Jika tiket valid dan status `BOOKED`, sistem menampilkan status **BOARDING GRANTED (HIJAU)** dan mengubah status tiket menjadi `BOARDED`.
   - Jika wajah tidak cocok, tiket tidak ada, atau sudah pernah digunakan, sistem menampilkan status **BOARDING DENIED (MERAH)** beserta alasannya.
5. Buka kembali halaman **Dashboard Admin** (`/admin.html`) untuk memantau pembaruan riwayat log boarding beserta detail skor kemiripan.

---

## 📡 Dokumentasi API Endpoint

### Backend Endpoints (Port 8000)

Swagger UI Interaktif: `http://localhost:8000/docs`

#### 🔐 Autentikasi (`/api/auth`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Pendaftaran akun penumpang baru | Publik |
| `POST` | `/api/auth/login` | Login user, menghasilkan Access Token JWT | Publik |
| `GET` | `/api/auth/me` | Mengambil data profil pengguna yang sedang login | Bearer Token |
| `GET` | `/api/auth/admin/check` | Verifikasi hak akses admin | Admin |
| `GET` | `/api/auth/admin/users` | Daftar seluruh akun pengguna & status pendaftaran wajah | Admin |
| `DELETE` | `/api/auth/admin/users/{user_id}` | Menghapus akun pengguna beserta data terkait secara kaskad | Admin |

#### 👤 Face Enrollment (`/api/face`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/face/enroll` | Mengunggah foto wajah dan menyimpan embedding 512-dim ke MySQL | Bearer Token |

#### 🎟️ Tiket & Perjalanan (`/api/tickets`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tickets/trains` | Mengambil daftar perjalanan kereta yang tersedia | Bearer Token |
| `POST` | `/api/tickets/book` | Melakukan pemesanan tiket perjalanan kereta | Bearer Token |
| `GET` | `/api/tickets/my-tickets` | Mengambil seluruh e-ticket milik pengguna yang sedang login | Bearer Token |

#### 🚪 Boarding Verification & Scanner (`/api/boarding`)
| Method | Endpoint | Deskripsi | Akses |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/boarding/scan` | Verifikasi boarding otomatis real-time melalui tangkapan kamera | Admin |
| `POST` | `/api/boarding/dev-verify` | Simulasi pengujian boarding tanpa kamera (Development Mode) | Admin |
| `GET` | `/api/boarding/logs` | Mengambil 100 riwayat transaksi pemindaian gerbang boarding | Admin |

---

### AI Service Endpoints (Port 8001 - Internal)

Swagger UI Internal: `http://localhost:8001/docs`  
*Seluruh endpoint di bawah ini dilindungi header wajib: `X-AI-Key: <AI_SERVICE_KEY>`*

| Method | Endpoint | Payload / Params | Deskripsi |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | - | Health check status model YOLO & ArcFace |
| `POST` | `/ai/embed` | `file`: Multipart Form Image | Mendeteksi wajah (YOLO) dan menghasilkan vektor 512 angka (ArcFace) |
| `POST` | `/ai/match` | JSON `{embedding, candidates}` | Membandingkan embedding probe dengan daftar embedding database (Cosine Similarity) |

---

## ❓ Troubleshooting & FAQ

### 1. Error: "AI Sakha tidak dapat dihubungi" saat Enroll atau Scan
- **Penyebab**: Layanan `ai_service` belum dijalankan di Port 8001.
- **Solusi**: Buka terminal baru, masuk ke direktori `ai_service`, dan jalankan:
  ```powershell
  uvicorn src.api:app --host 127.0.0.1 --port 8001
  ```

### 2. Error: "Autentikasi internal AI gagal (HTTP 401)"
- **Penyebab**: Nilai `AI_SERVICE_KEY` di file `.env` root tidak cocok dengan `AI_API_KEY` di `ai_service/.env`.
- **Solusi**: Samakan nilai kedua variabel tersebut lalu restart kedua server.

### 3. Kamera / Webcam Tidak Muncul di Browser
- **Penyebab**: Browser memblokir izin akses webcam atau webcam sedang digunakan oleh aplikasi lain (seperti Zoom/Teams).
- **Solusi**: Klik ikon gembok / kamera di *address bar* browser, izinkan akses kamera untuk `localhost`, dan pastikan aplikasi lain yang menggunakan kamera sudah ditutup.

### 4. Jadwal Kereta Tidak Muncul di Halaman Pemesanan
- **Penyebab**: Tabel `trains` masih kosong atau seluruh jadwal telah lewat dari waktu saat ini.
- **Solusi**: Jalankan script `python backend/seed_jadwal_kereta.py` dan masukkan tanggal hari ini atau beberapa hari ke depan.

### 5. InsightFace Gagal Mengunduh Bobot Model Pertama Kali
- **Penyebab**: Masalah koneksi jaringan saat mengunduh paket `buffalo_l`.
- **Solusi**: Pastikan koneksi internet stabil. InsightFace akan mengunduh model ke direktori cache lokal (`~/.insightface/models/buffalo_l`).

---

## 👥 Pengembang

Proyek ini dikembangkan untuk kebutuhan praktikum mata kuliah **Machine Learning** - Sistem Smart Boarding Gate Berbasis Face Recognition:
- **Barra** — *Backend Architecture, Database Modeling, REST API & Frontend Web UI KAI RailGate*
- **Sakha** — *AI Engine, Face Detection (YOLOv8-Face), Feature Extraction (ArcFace InsightFace) & Similarity Matching*

---
<div align="center">
  <sub>Dibuat dengan ❤️ untuk kemajuan sistem perkeretaapian Indonesia.</sub>
</div>
