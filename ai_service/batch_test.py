import csv
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# =========================================
# KONFIGURASI
# =========================================

load_dotenv()

API_URL = "http://127.0.0.1:8001"
API_KEY = os.getenv("AI_API_KEY")

DATASET = Path("dataset")
ENROLLMENT = DATASET / "enrollment"
VALIDATION = DATASET / "validation"

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

EXTENSIONS = {".jpg", ".jpeg", ".png"}

if not API_KEY:
    raise RuntimeError("AI_API_KEY belum diatur di .env")

HEADERS = {
    "X-AI-Key": API_KEY
}

session = requests.Session()


# =========================================
# FUNGSI AMBIL FOTO
# =========================================

def get_images(folder):
    if not folder.exists():
        return []

    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    )


# =========================================
# FUNGSI EMBEDDING
# =========================================

def get_embedding(image_path):
    try:
        mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        with open(image_path, "rb") as image:
            response = session.post(
                f"{API_URL}/ai/embed",
                headers=HEADERS,
                files={
                    "file": (
                        image_path.name,
                        image,
                        mime_type
                    )
                },
                timeout=120
            )

        response.raise_for_status()
        data = response.json()

        if data.get("ok") is not True:
            print(
                f"[SKIP] {image_path.name}: "
                f"{data.get('reason', 'UNKNOWN')}"
            )
            return None

        embedding = data.get("embedding")

        if not isinstance(embedding, list) or len(embedding) != 512:
            print(f"[ERROR] Dimensi embedding: {image_path}")
            return None

        return embedding

    except (requests.RequestException, ValueError) as error:
        print(f"[ERROR] {image_path}: {error}")
        return None


# =========================================
# FUNGSI MATCHING
# =========================================

def match_face(embedding, candidates):
    payload = {
        "embedding": embedding,
        "candidates": candidates
    }

    response = session.post(
        f"{API_URL}/ai/match",
        headers=HEADERS,
        json=payload,
        timeout=120
    )

    response.raise_for_status()
    return response.json()


# =========================================
# MAIN PROGRAM
# =========================================

def main():
    print("\n=== BATCH TEST FACE RECOGNITION ===\n")

    candidates = []
    enrolled_users = set()
    user_folders = sorted(
        p for p in ENROLLMENT.iterdir() if p.is_dir()
    )

    # 1. Membuat galeri kandidat
    print("[1] Membaca dataset enrollment...")

    for user_folder in user_folders:
        user_id = user_folder.name

        for image_path in get_images(user_folder):
            embedding = get_embedding(image_path)

            if embedding is None:
                continue

            candidates.append({
                "user_id": user_id,
                "embedding": embedding
            })

            enrolled_users.add(user_id)

            print(f"[ENROLLED] {user_id}: {image_path.name}")

    if not candidates:
        print("Tidak ada embedding enrollment yang valid.")
        return

    print(f"\nTotal identitas: {len(enrolled_users)}")
    print(f"Total embedding referensi: {len(candidates)}")

    # 2. Menguji dataset validation
    print("\n[2] Menjalankan face matching...")

    rows = []
    correct = 0
    total = 0

    validation_folders = sorted(
        p for p in VALIDATION.iterdir() if p.is_dir()
    )

    for user_folder in validation_folders:
        actual_user = user_folder.name

        for image_path in get_images(user_folder):
            embedding = get_embedding(image_path)

            if embedding is None:
                rows.append({
                    "file": str(image_path),
                    "actual": actual_user,
                    "predicted": "",
                    "matched": False,
                    "similarity": "",
                    "runner_up_similarity": "",
                    "reason": "EMBED_FAILED",
                    "correct": False
                })
                continue

            try:
                result = match_face(embedding, candidates)
            except (requests.RequestException, ValueError) as error:
                print(f"[ERROR MATCH] {image_path}: {error}")
                rows.append({
                    "file": str(image_path),
                    "actual": actual_user,
                    "predicted": "",
                    "matched": False,
                    "similarity": "",
                    "runner_up_similarity": "",
                    "reason": "API_ERROR",
                    "correct": False
                })
                continue

            predicted = (
                result.get("user_id")
                if result.get("matched") is True
                else None
            )

            is_correct = predicted == actual_user
            total += 1
            correct += int(is_correct)

            row = {
                "file": str(image_path),
                "actual": actual_user,
                "predicted": predicted or "UNKNOWN",
                "matched": result.get("matched"),
                "similarity": result.get("similarity"),
                "runner_up_similarity": result.get(
                    "runner_up_similarity"
                ),
                "reason": result.get("reason"),
                "correct": is_correct
            }

            rows.append(row)

            status = "BENAR" if is_correct else "SALAH"

            print(
                f"[{status}] {image_path.name} | "
                f"Actual={actual_user} | "
                f"Predicted={predicted or 'UNKNOWN'} | "
                f"Similarity={result.get('similarity')}"
            )

    # 3. Menyimpan hasil
    csv_path = RESULTS / "batch_results.csv"

    fields = [
        "file",
        "actual",
        "predicted",
        "matched",
        "similarity",
        "runner_up_similarity",
        "reason",
        "correct"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # 4. Ringkasan
    print("\n=== HASIL BATCH TEST ===")
    print(f"Total matching berhasil diproses: {total}")
    print(f"Prediksi identitas benar: {correct}")
    print(f"Total file dicatat: {len(rows)}")

    if total > 0:
        accuracy = correct / total * 100
        print(f"Akurasi pada sampel terproses: {accuracy:.2f}%")
    else:
        print("Belum ada hasil matching yang dapat dievaluasi.")

    print(f"Hasil tersimpan di: {csv_path}")


if __name__ == "__main__":
    main()