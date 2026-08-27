"""音声ファイル出力API（STEP 10 / 13: WAV / MP3 / FLAC）。"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.state import GENERATION_CACHE
from app.export.exporter import ExportError, export_audio

router = APIRouter(prefix="/api", tags=["export"])

MEDIA_TYPES = {"wav": "audio/wav", "mp3": "audio/mpeg", "flac": "audio/flac"}


@router.post("/bgm/{generation_id}/export")
async def export_bgm(generation_id: str, format: str = "wav") -> FileResponse:
    if format not in MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="対応していない出力形式です。wav / mp3 / flac のいずれかを指定してください。")

    cached = GENERATION_CACHE.get(generation_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="生成結果が見つかりません。再度BGMを生成してください。")

    try:
        # WAVの書き込みやffmpegでのMP3変換はCPU/IO律速のためスレッドに逃がす
        path = await asyncio.to_thread(export_audio, cached.audio, cached.sr, generation_id, format)
    except ExportError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return FileResponse(path, media_type=MEDIA_TYPES[format], filename=path.name)
