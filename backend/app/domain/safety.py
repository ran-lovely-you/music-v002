"""安全設計に関わる共通定義。

- 音楽生成AIへの既定ネガティブプロンプト（STEP 7）
- 医学的断定表現のフィルタ（STEP 1 / 14 の方針: 予防・治療・改善の断定を行わない）
"""
from __future__ import annotations

import re

# 音楽生成AIに渡す既定のネガティブプロンプト（高齢者向け安全設計のため）
DEFAULT_NEGATIVE_PROMPT_TERMS: list[str] = [
    "aggressive",
    "harsh sound",
    "sudden loud sound",
    "heavy bass",
    "distorted sound",
    "intense percussion",
    "frightening atmosphere",
    "chaotic rhythm",
    "extreme dynamics",
    "sharp high frequencies",
    "horror",
    "disturbing sound",
    "screeching",
    "abrupt volume changes",
    "loud crash",
    "jump scare sound",
    "industrial noise",
]

# 医学的断定表現（禁止ワード）。生成テキスト（YouTube説明文・タイトル案等）から必ず除外する。
MEDICAL_CLAIM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"認知症.{0,4}(予防|治療|改善|治る|治す)",
        r"(記憶力|脳機能).{0,4}(必ず)?(改善|向上|回復)する",
        r"病気.{0,4}(治る|治す)",
        r"cure(s)?\s+dementia",
        r"prevent(s)?\s+dementia",
        r"improves?\s+memory\s+(function|loss)?",
        r"medically\s+proven",
        r"clinically\s+proven",
        r"治療効果",
        r"医学的に(証明|保証)",
    ]
]

SAFE_REPLACEMENT_PHRASES = [
    "認知機能サポート",
    "リラックス",
    "集中環境",
    "穏やかな生活環境",
]


def contains_medical_claim(text: str) -> bool:
    return any(p.search(text) for p in MEDICAL_CLAIM_PATTERNS)


def sanitize_medical_claims(text: str) -> str:
    """医学的断定表現を検出した場合、安全な表現へ置き換える防御的フィルタ。

    このアプリの生成ロジックは元々こうした表現を作らない設計だが、
    将来の拡張や外部入力混入に備えた最終防御ラインとして実装する。
    """
    sanitized = text
    for pattern in MEDICAL_CLAIM_PATTERNS:
        if pattern.search(sanitized):
            sanitized = pattern.sub("穏やかな生活環境をサポート", sanitized)
    return sanitized


def build_negative_prompt(extra_terms: list[str] | None = None) -> str:
    terms = list(DEFAULT_NEGATIVE_PROMPT_TERMS)
    if extra_terms:
        for t in extra_terms:
            if t not in terms:
                terms.append(t)
    return ", ".join(terms)
