"""ElevenLabs Music API 用アダプタ（外部AI音楽生成サービス、任意）。

APIキーが .env に設定されている場合のみ利用可能。
キーはログに一切出力しない。通信エラー時も秘密情報を含まないメッセージのみを返す。
"""
from __future__ import annotations

import io

import httpx
import numpy as np
import soundfile as sf

from app.config import settings
from app.domain.models import GenerateRequest
from app.music_providers.base import MusicProvider, ProviderError


class ElevenLabsMusicProvider(MusicProvider):
    name = "elevenlabs"
    requires_api_key = True
    API_URL = "https://api.elevenlabs.io/v1/music"

    async def generate(
        self,
        request: GenerateRequest,
        prompt_text: str,
        negative_prompt: str,
        seed: int | None = None,
    ) -> tuple[np.ndarray, int]:
        api_key = settings.elevenlabs_api_key
        if not api_key:
            raise ProviderError(
                "ElevenLabs の APIキーが設定されていません。.env の ELEVENLABS_API_KEY を"
                "設定するか、procedural プロバイダー（APIキー不要）をご利用ください。"
            )
        headers = {"xi-api-key": api_key}
        payload = {
            "prompt": prompt_text,
            "negative_prompt": negative_prompt,
            "duration_seconds": request.duration_sec,
            "output_format": "wav",
        }
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(self.API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                audio_bytes = resp.content
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"ElevenLabs API がエラーを返しました（HTTP {exc.response.status_code}）。"
                "しばらくしてから再度お試しください。"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("ElevenLabs API への接続に失敗しました。ネットワークをご確認ください。") from exc

        data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=True)
        return data.T, sr
