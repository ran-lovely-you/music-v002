"""Stability AI Audio API 用アダプタ（外部AI音楽生成サービス、任意）。

APIキーが .env に設定されている場合のみ利用可能。
"""
from __future__ import annotations

import io

import httpx
import numpy as np
import soundfile as sf

from app.config import settings
from app.domain.models import GenerateRequest
from app.music_providers.base import MusicProvider, ProviderError


class StabilityMusicProvider(MusicProvider):
    name = "stability"
    requires_api_key = True
    API_URL = "https://api.stability.ai/v2beta/audio/stable-audio-2/generate"

    async def generate(
        self,
        request: GenerateRequest,
        prompt_text: str,
        negative_prompt: str,
        seed: int | None = None,
    ) -> tuple[np.ndarray, int]:
        api_key = settings.stability_api_key
        if not api_key:
            raise ProviderError(
                "Stability AI の APIキーが設定されていません。.env の STABILITY_API_KEY を"
                "設定するか、procedural プロバイダー（APIキー不要）をご利用ください。"
            )
        headers = {"authorization": f"Bearer {api_key}", "accept": "audio/*"}
        data = {
            "prompt": prompt_text,
            "negative_prompt": negative_prompt,
            "duration": min(request.duration_sec, 190),
            "seed": seed or 0,
        }
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(self.API_URL, headers=headers, data=data, files={"none": ""})
                resp.raise_for_status()
                audio_bytes = resp.content
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Stability AI API がエラーを返しました（HTTP {exc.response.status_code}）。"
                "しばらくしてから再度お試しください。"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("Stability AI API への接続に失敗しました。ネットワークをご確認ください。") from exc

        data_arr, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=True)
        return data_arr.T, sr
