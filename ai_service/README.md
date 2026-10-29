# Sakha — Starter Kit AI Face Recognition Tiket Dummy

Tujuan: YOLO face detection + ArcFace (InsightFace buffalo_l) + webcam test + API AI agar bisa diintegrasikan ke FastAPI utama/MySQL milik Barra.

## 0. Ketentuan
- Windows PowerShell, Python 3.11 (64-bit), VS Code, Git.
- Model YOLO **wajah**, bukan `yolov8n.pt` COCO yang mendeteksi object/person.
- Bobot ArcFace `buffalo_l` di-download pada first run melalui InsightFace (~326 MB).
- Penggunaan pretrained InsightFace hanya untuk riset non-komersial; Ultralytics AGPL-3.0 memiliki kewajiban lisensi.
- Mesin demo bisa menggunakan CPU. GPU NVIDIA opsional dan mengikuti selector PyTorch.
- `YOLO -> cropped region -> InsightFace landmark detection+alignment -> ArcFace embedding`. Deteksi dua tahap untuk MVP, bukan pipeline paling optimal.

## 1. Setup
Buka PowerShell:
```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Ubah `AI_API_KEY` di `.env` menjadi string random panjang, jangan commit `.env`.

Jika aktivasi PowerShell diblokir, untuk jendela terminal saat ini:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Bobot YOLO
Download model YOLOv8-face dari komunitas model `junjiang/GestureFace`:
```powershell
Invoke-WebRequest -Uri "https://huggingface.co/junjiang/GestureFace/resolve/main/yolov8n-face.pt" -OutFile "models/yolov8n-face.pt"
```
Alternatif periksa weights di https://github.com/akanametov/yolo-face/releases, lalu copy `yolov8n-face.pt` ke `models/`. Bobot pihak ketiga harus diperiksa kompatibilitasnya dengan paket `ultralytics` yang terpasang, termasuk format deteksi/pose.

Tes detektor:
```powershell
yolo predict model=models/yolov8n-face.pt source=0 show=True conf=0.5 imgsz=640
```
Tekan Q / tutup jendela untuk selesai. Ini hanya memeriksa kotak deteksi wajah.

## 3. Tes embedding ArcFace (3-5 foto per peserta)
Simpan foto milik peserta yang setuju di `test_images/` dan jalankan dari root proyek:
```powershell
python -m scripts.local_enroll --user sakha --image test_images/sakha1.jpg
python -m scripts.local_enroll --user sakha --image test_images/sakha2.jpg
python -m scripts.local_enroll --user sakha --image test_images/sakha3.jpg
python -m scripts.local_enroll --user barra --image test_images/barra1.jpg
python -m scripts.local_enroll --user barra --image test_images/barra2.jpg
python -m scripts.local_enroll --user barra --image test_images/barra3.jpg
```
`data/dev_gallery.json` berisi embeddings demo dan tidak boleh dipush. Jika pengen reset demo, hapus file ini.

## 4. Scan webcam lokal
```powershell
python -m scripts.camera_demo
```
Tekan Q untuk keluar. **Tampilan hanya menunjukkan identitas; tiket belum diverifikasi**.

## 5. Tes API (Sakha)
```powershell
python -m uvicorn src.api:app --host 127.0.0.1 --port 8001
```
Buka http://127.0.0.1:8001/docs untuk Swagger UI.

Di terminal PowerShell baru dengan venv aktif:
```powershell
$env:AI_TOKEN = (Get-Content .env | Where-Object { $_ -like 'AI_API_KEY=*' }) -replace '^AI_API_KEY=', ''
curl.exe -X POST "http://127.0.0.1:8001/ai/embed" -H "X-AI-Key: $env:AI_TOKEN" -F "file=@test_images/sakha1.jpg"
```
Respons berisi 512 dimensi embedding jika berhasil; jangan tampilkan semua embedding di UI publik.

Untuk uji match, gunakan Swagger `/ai/match` atau panggil API dari backend milik Barra. Format ada di `docs/CONTRACT.md`.

## 6. Test otomasi
```powershell
python -m pytest -q
python -m pip freeze > requirements.lock.txt
```
`requirements.lock.txt` berguna sebagai snapshot environment yang berfungsi di laptop ini. Angka threshold bukan bukti akurasi, perlu pengujian di data wajah asli.

## 7. Kerja bareng Barra
- Komit proyek ini ke branch `sakha/ai-engine`, tanpa gambar wajah, embedding, model dan `.env`.
- Kontrak API ke Barra: `docs/CONTRACT.md`.
- Saat dua laptop terhubung WiFi yang sama, barulah jalankan `--host 0.0.0.0` dan akses pakai IPv4 laptop Sakha, serta izinkan port pada Windows Firewall **hanya jaringan private/laptop Barra**. Lebih aman gunakan jaringan privat yang terpercaya dan HTTPS/VPN jika bisa.
- Backend Barra tidak perlu memasang YOLO/InsightFace/MySQL di laptop Sakha.
- Webcam bisa dipakai lokal di laptop Sakha; untuk boarding sungguhan, scanner memanggil endpoint `/api/boarding/scan` milik Barra dan menampilkan status yang dikembalikannya.

## 8. Batasan dan prasyarat sebelum demo final
- Belum ada liveness. Wajah dari foto/layar mungkin dikenali.
- Dua detektor (YOLO + model deteksi InsightFace pada ROI) lambat namun lebih mudah diuji; optimasi nanti setelah fungsional.
- Demo saat ini belum melakukan checkout tiket dan belum mengakses MySQL, sesuai pembagian tugas Sakha/Barra.
- Confidence YOLO != similarity ArcFace != status valid tiket.
- Tampilannya **tidak** mengklaim face match sebagai otorisasi boarding.
