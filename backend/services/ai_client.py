
import os
import math
import struct
import httpx

from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv(
    Path(__file__).resolve().parents[2] / ".env",
    override=True
)

AI_SERVICE_URL = os.getenv(
    "AI_SERVICE_URL",
    "http://127.0.0.1:8001"
)

AI_SERVICE_KEY = os.getenv("AI_SERVICE_KEY")


def validate_vector(values):
    if not isinstance(values, list) or len(values) != 512:
        raise ValueError("Embedding harus 512 angka")

    if not all(
        type(v) in (int, float) and math.isfinite(v)
        for v in values
    ):
        raise ValueError("Embedding mengandung nilai tidak valid")

    return struct.pack("<512f", *values)


def ai_headers():
    if not AI_SERVICE_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI_SERVICE_KEY belum dikonfigurasi"
        )

    return {"X-AI-Key": AI_SERVICE_KEY}


async def generate_embedding(
    image_bytes: bytes,
    content_type: str = "image/jpeg"
):
    if content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=415,
            detail="Hanya mendukung JPEG atau PNG"
        )

    if not image_bytes or len(image_bytes) > 4 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Ukuran gambar harus 1 byte sampai 4 MB"
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL.rstrip('/')}/ai/embed",
                headers=ai_headers(),
                files={
                    "file": (
                        "face.png" if content_type == "image/png"
                        else "face.jpg",
                        image_bytes,
                        content_type
                    )
                }
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="AI Sakha tidak dapat dihubungi"
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=502,
            detail="Autentikasi internal AI gagal"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"AI Sakha mengembalikan HTTP {response.status_code}"
        )

    try:
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError("Respons bukan JSON object")

        if result.get("ok") is not True:
            reason = result.get("reason", "UNKNOWN")
            raise HTTPException(
                status_code=422,
                detail=f"Wajah ditolak AI: {reason}"
            )

        embedding_bytes = validate_vector(
            result["embedding"]
        )

        model_version = result["model_version"]

        if (
            not isinstance(model_version, str)
            or not model_version.strip()
        ):
            raise ValueError("Versi model tidak valid")

    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, struct.error):
        raise HTTPException(
            status_code=502,
            detail="Format embedding AI Sakha tidak valid"
        )

    return {
        "embedding": embedding_bytes,
        "model_version": model_version,
        "box": result.get("box")
    }


async def match_face(embedding_bytes: bytes, candidates: list):
    if len(embedding_bytes) != 2048:
        raise HTTPException(
            status_code=422,
            detail="Embedding scanner tidak valid"
        )

    probe = list(struct.unpack("<512f", embedding_bytes))

    if not all(math.isfinite(x) for x in probe):
        raise HTTPException(
            status_code=422,
            detail="Embedding scanner tidak valid"
        )

    if not candidates:
        return {
            "matched": False,
            "user_id": None,
            "similarity": None,
            "reason": "EMPTY_GALLERY"
        }

    formatted = []
    ids = set()

    for candidate in candidates:
        raw = candidate["embedding"]

        if len(raw) != 2048:
            raise HTTPException(
                status_code=422,
                detail="Embedding database tidak valid"
            )

        values = list(struct.unpack("<512f", raw))

        if not all(math.isfinite(x) for x in values):
            raise HTTPException(
                status_code=422,
                detail="Embedding database tidak valid"
            )

        uid = str(candidate["user_id"])
        ids.add(uid)

        formatted.append({
            "user_id": uid,
            "embedding": values
        })

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL.rstrip('/')}/ai/match",
                headers=ai_headers(),
                json={
                    "embedding": probe,
                    "candidates": formatted
                }
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="AI Sakha tidak dapat dihubungi"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Matching AI gagal (HTTP {response.status_code})"
        )

    try:
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError()

        matched = result["matched"]

        if type(matched) is not bool:
            raise ValueError()

        score = result.get("similarity")

        if score is not None and (
            type(score) not in (int, float)
            or not math.isfinite(score)
            or not -1 <= score <= 1
        ):
            raise ValueError()

        if matched:
            uid = result["user_id"]

            if not isinstance(uid, str) or uid not in ids:
                raise ValueError()

            if score is None:
                raise ValueError()

            result["user_id"] = int(uid)

        else:
            result["user_id"] = None

        return result

    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Respons matching AI tidak valid"
        )
