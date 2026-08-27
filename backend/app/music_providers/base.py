"""MusicProvider インターフェース（STEP 8）。

特定のAI音楽生成サービスに依存しないよう、共通インターフェースの下に
複数のプロバイダー実装（procedural / elevenlabs / stability 等）を配置する。
新しいAIサービスは、このインターフェースを実装するアダプタを追加するだけでよい。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.domain.models import GenerateRequest


class ProviderError(Exception):
    """プロバイダー起因のエラー。APIキー未設定・API通信失敗などをユーザーに分かりやすく伝える。"""


class MusicProvider(ABC):
    name: str = "base"
    requires_api_key: bool = False

    @abstractmethod
    async def generate(
        self,
        request: GenerateRequest,
        prompt_text: str,
        negative_prompt: str,
        seed: int | None = None,
    ) -> tuple[np.ndarray, int]:
        """BGMを生成する。

        戻り値: (stereo_audio[2, N] float32 (-1.0〜1.0), sample_rate)
        """
        raise NotImplementedError
