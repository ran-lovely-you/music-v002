"""APIキー不要で実際に動作するローカル音楽生成プロバイダー（デフォルト）。"""
from __future__ import annotations

import asyncio

import numpy as np

from app.audio.synthesis import generate_raw_bgm
from app.domain.models import GenerateRequest
from app.music_providers.base import MusicProvider


class ProceduralMusicProvider(MusicProvider):
    name = "procedural"
    requires_api_key = False

    async def generate(
        self,
        request: GenerateRequest,
        prompt_text: str,
        negative_prompt: str,
        seed: int | None = None,
    ) -> tuple[np.ndarray, int]:
        # CPU律速の合成処理はスレッドに逃がし、生成中もサーバーが他のリクエストに応答できるようにする
        return await asyncio.to_thread(generate_raw_bgm, request, seed)
