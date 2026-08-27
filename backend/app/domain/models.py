"""ドメインモデル（Pydanticスキーマ）。

医学的効果（認知症予防・治療・記憶力改善 等）を断定する文言は
このアプリのどの層でも生成しない方針を、型レベルのコメントとしても明記する。
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BgmType(str, Enum):
    MORNING = "morning"          # A. 朝の目覚め
    DAYTIME_RELAX = "daytime"    # B. 昼間のリラックス
    FOCUS = "focus"               # C. 集中・軽い認知活動
    REMINISCENCE = "reminiscence"  # D. 回想・思い出
    FOREST_NATURE = "forest"      # E. 森・自然
    NIGHT_SLEEP = "night"         # F. 夜・睡眠前
    MYSTIC_FOREST = "mystic_forest"  # G. 神秘的な森


class TempoLevel(str, Enum):
    VERY_SLOW = "very_slow"   # とてもゆっくり
    SLOW = "slow"              # ゆっくり
    GENTLE = "gentle"          # 穏やか
    NORMAL = "normal"          # 普通


class Mood(str, Enum):
    HEALING = "healing"        # 癒やし
    CALM = "calm"               # 穏やか
    BRIGHT = "bright"           # 明るい
    REASSURING = "reassuring"   # 安心
    MYSTIC = "mystic"           # 神秘的
    NATURAL = "natural"         # 自然
    NOSTALGIC = "nostalgic"     # 懐かしい
    FOCUS = "focus"             # 集中
    SLEEP = "sleep"             # 睡眠
    HOPEFUL = "hopeful"         # 希望


class Instrument(str, Enum):
    PIANO = "piano"
    HARP = "harp"
    MUSIC_BOX = "music_box"          # オルゴール
    ACOUSTIC_GUITAR = "acoustic_guitar"
    FLUTE = "flute"
    CLARINET = "clarinet"
    MARIMBA = "marimba"
    SOFT_STRINGS = "soft_strings"
    PAD = "pad"
    BELL = "bell"
    CHIME = "chime"


class NatureSound(str, Enum):
    RAIN = "rain"
    RIVER = "river"
    WAVES = "waves"
    FOREST = "forest"
    BIRDS = "birds"
    WIND = "wind"
    CAMPFIRE = "campfire"


DURATION_CHOICES_SEC = [300, 600, 900, 1800, 3600, 7200]  # 5/10/15/30/60/120分

TEMPO_BPM_RANGE: dict[TempoLevel, tuple[int, int]] = {
    TempoLevel.VERY_SLOW: (40, 55),
    TempoLevel.SLOW: (56, 68),
    TempoLevel.GENTLE: (69, 80),
    TempoLevel.NORMAL: (81, 92),
}


class GenerateRequest(BaseModel):
    bgm_type: BgmType
    moods: list[Mood] = Field(default_factory=list, max_length=4)
    instruments: list[Instrument] = Field(default_factory=list, max_length=6)
    nature_sounds: list[NatureSound] = Field(default_factory=list, max_length=4)
    duration_sec: int = 300
    tempo_level: TempoLevel = TempoLevel.GENTLE
    bpm: Optional[int] = None
    provider: Optional[str] = None
    title: Optional[str] = None
    for_elderly_care: bool = True

    @field_validator("duration_sec")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v not in DURATION_CHOICES_SEC:
            raise ValueError(f"duration_sec must be one of {DURATION_CHOICES_SEC}")
        return v

    @field_validator("bpm")
    @classmethod
    def validate_bpm(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (30 <= v <= 100):
            raise ValueError("bpm must be between 30 and 100 for elderly-friendly BGM")
        return v

    def resolved_bpm(self) -> int:
        if self.bpm:
            return self.bpm
        lo, hi = TEMPO_BPM_RANGE[self.tempo_level]
        return (lo + hi) // 2


class PromptSet(BaseModel):
    short: str
    detailed: str
    professional: str
    negative: str


class SafetyCheckItem(BaseModel):
    key: str
    label: str
    status: str  # "green" | "yellow" | "red"
    message: str


class SafetyReport(BaseModel):
    overall_status: str  # "green" | "yellow" | "red"
    items: list[SafetyCheckItem]


class AnalysisResult(BaseModel):
    duration_sec: float
    sample_rate: int
    peak_dbfs: float
    rms_dbfs: float
    lufs_integrated: Optional[float]
    clipping_detected: bool
    clipping_sample_count: int
    high_freq_energy_ratio: float
    low_freq_energy_ratio: float
    max_short_term_dynamic_jump_db: float
    rhythm_intensity: float
    silence_ratio: float


class ScoreBreakdown(BaseModel):
    relaxation: float
    listenability: float
    volume_stability: float
    tonal_balance: float
    long_duration_suitability: float
    naturalness: float
    elderly_fit: float


class QualityScore(BaseModel):
    total: float
    breakdown: ScoreBreakdown
    disclaimer: str = (
        "本スコアは音響・コンテンツ設計上の参考値であり、"
        "医学的な効果や認知機能改善を保証するものではありません。"
    )


class GenerationResult(BaseModel):
    generation_id: str
    request: GenerateRequest
    prompts: PromptSet
    preview_url: str
    analysis: AnalysisResult
    safety: SafetyReport
    score: QualityScore
    provider_used: str


class ProjectRecord(BaseModel):
    id: str
    title: str
    created_at: str
    bgm_type: BgmType
    bpm: int
    instruments: list[Instrument]
    nature_sounds: list[NatureSound]
    prompts: PromptSet
    analysis: AnalysisResult
    safety: SafetyReport
    score: QualityScore
    audio_path: str


class YoutubeMetadata(BaseModel):
    titles: list[str]
    description: str
    tags: list[str]
    hashtags: list[str]
    thumbnail_prompt: str
    intro_text: str
