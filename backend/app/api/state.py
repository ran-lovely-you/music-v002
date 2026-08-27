"""生成結果の一時キャッシュ（プロセス内メモリ）。

プレビュー再生・書き出し・プロジェクト保存で同じ音声データを再利用するために使う。
永続化が必要なデータ（プロジェクト情報）は SQLite 側に保存する。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.models import GenerationResult


@dataclass
class CachedGeneration:
    audio: np.ndarray
    sr: int
    result: GenerationResult


GENERATION_CACHE: dict[str, CachedGeneration] = {}
