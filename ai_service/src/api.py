"""Sakha internal face-AI API. This service must NOT be exposed publicly."""
import hmac
import os
from functools import lru_cache

import cv2
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile, Depends
from pydantic import BaseModel, Field

from src.face_engine import FaceEngine, compare_embeddings

load_dotenv()
app = FastAPI(title='Sakha Face AI (internal)', version='0.1.0')
MAX_IMAGE_BYTES = 4 * 1024 * 1024


def require_key(x_ai_key: str | None = Header(default=None)):
    expected = os.getenv('AI_API_KEY', '')
    if not expected or not x_ai_key or not hmac.compare_digest(x_ai_key, expected):
        raise HTTPException(status_code=401, detail='Unauthorized')


@lru_cache(maxsize=1)
def engine():
    return FaceEngine()


class Candidate(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    embedding: list[float] = Field(min_length=512, max_length=512)


class MatchBody(BaseModel):
    embedding: list[float] = Field(min_length=512, max_length=512)
    candidates: list[Candidate]


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'sakha-ai', 'model_loaded': engine.cache_info().currsize > 0}


@app.post('/ai/embed', dependencies=[Depends(require_key)])
async def embed(file: UploadFile = File(...)):
    if file.content_type not in ('image/jpeg', 'image/png'):
        raise HTTPException(415, detail='Hanya PNG/JPEG')
    raw = await file.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(413, detail='Image melebihi 4MB')
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, detail='File bukan image valid')
    return engine().embed(frame)


@app.post('/ai/match', dependencies=[Depends(require_key)])
def match(body: MatchBody):
    try:
        candidates = [{'user_id': item.user_id, 'embedding': item.embedding}
                      for item in body.candidates]
        return compare_embeddings(body.embedding, candidates,
                                  threshold=float(os.getenv('MATCH_THRESHOLD', '0.50')),
                                  margin=float(os.getenv('MATCH_MARGIN', '0.04')))
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
