# Kontrak API Sakha (AI) <> Barra (Backend)

## Keputusan arsitektur
- AI Sakha TIDAK mengakses database, memvalidasi tiket, atau menetapkan boarding secara langsung.
- Barra menyimpan `users`, `face_embeddings`, `trains`, `tickets`, `boarding_logs` di MySQL.
- Semua panggilan AI berasal dari backend Barra, bukan browser publik.
- Header wajib `X-AI-Key: <TOKEN>` untuk POST AI. HTTPS/VPN/trusted LAN untuk koneksi lintas mesin.
- User ID dibuat di MySQL oleh Barra; embedding ArcFace adalah 512 angka float, bukan label manual.

## POST /ai/embed (multipart/form-data)
- Field `file`: 1 JPEG/PNG, <=4MB, tepat satu wajah jelas.
- Sukses: `{ "ok": true, "reason":"OK", "embedding":[512 angka], "box":[x1,y1,x2,y2], "faces_detected":1, "blur_score": 123.4 }`
- Ditolak: `{ "ok": false, "reason":"NO_FACE|MULTIPLE_FACES|FACE_TOO_SMALL|BLURRY|LANDMARK_NOT_FOUND|..." }`
- HTTP 401 unauthorized, 413 >4 MB, 415 bukan JPEG/PNG, 400 gambar rusak.
- Alur enrollment: Barra memanggil endpoint ini untuk 3-5 foto milik user berizin, menyimpan 3-5 embeddings per akun MySQL. Jangan simpan foto jika tidak dibutuhkan.

## POST /ai/match (application/json)
Body:
```
{
  "embedding": [512 angka dari /ai/embed saat scan],
  "candidates": [
    {"user_id":"user_1", "embedding":[512 angka]},
    {"user_id":"user_1", "embedding":[512 angka]},
    {"user_id":"user_2", "embedding":[512 angka]}
  ]
}
```
Balasan:
```
{"matched":true, "user_id":"user_1", "similarity":0.68,
 "runner_up_similarity":0.19,"reason":"MATCH"}
```
- Nilai similarity adalah cosine [-1,1], **bukan persen probabilitas**.
- Threshold 0.50 dan margin 0.04 hanya contoh awal; tentukan berdasarkan uji validasi wajah sungguhan, dan antisipasi spoofing.
- Banyak embedding per user didukung; skor terbaik per user dipakai sebelum menghitung margin antarpengguna.

## Pekerjaan Barra yang dipanggil dari scanner
Barra membuat endpoint di backend UTAMA (contoh kontrak):
`POST /api/boarding/scan` -> multipart foto webcam (operator terautentikasi).
1. Barra -> AI `/ai/embed`.
2. Jika wajah gagal, tampilkan kuning/tolak dan jangan ada boarding.
3. Barra ambil daftar embedding aktif dari MySQL.
4. Barra -> AI `/ai/match` menggunakan embedding scan dan galeri dari DB.
5. Jika `matched=false`, return `UNKNOWN_FACE` (merah).
6. Jika cocok, cari tiket milik user untuk perjalanan/sesi gate saat itu.
7. Validasi tiket: paid/active (dummy), tanggal/jadwal/stasiun cocok, belum digunakan.
8. Lock row tiket + update used_at + insert boarding_log DALAM SATU transaksi DB; cegah dua scan bersamaan menggunakan unique/event key bila perlu.
9. Return `{status:"GREEN|RED|YELLOW", code:"BOARDING_ALLOWED|NO_VALID_TICKET|...", message:"..."}`.
10. Ubah status user UI berdasarkan balasan backend; **jangan gunakan kecocokan wajah saja untuk indikator hijau**.

## Status contoh
- GREEN: cocok wajah + tiket valid + belum dipakai + (liveness valid apabila fitur diaktifkan)
- RED: unknown face, tiket tidak ada, kedaluwarsa, salah perjalanan, sudah dipakai, spoofing
- YELLOW: wajah blur, lebih dari satu wajah, posisi tak jelas, koneksi backend gagal

## Catatan keamanan
- Endpoint /ai/embed dan /ai/match harus private. Jangan buka ke internet secara langsung.
- Non-commercial academic demo only until model licenses and privacy requirements are addressed.
- Foto, embedding, log wajah adalah data sensitif. Consent dan kontrol penghapusan diperlukan.
- Belum ada liveness/anti-spoofing. Foto dari layar atau cetakan berpotensi lolos; jangan hubungkan ke gerbang fisik.
- Threshold harus dikalibrasi dari uji identitas berbeda, kondisi cahaya, pose dan perangkat.
