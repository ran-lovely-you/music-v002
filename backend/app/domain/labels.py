"""GUI表示用の日本語ラベル定義（STEP 15 / 21: 日本語UI）。"""
from __future__ import annotations

from app.domain.models import Instrument, Mood, NatureSound, TempoLevel

MOOD_JA: dict[Mood, str] = {
    Mood.HEALING: "癒やし",
    Mood.CALM: "穏やか",
    Mood.BRIGHT: "明るい",
    Mood.REASSURING: "安心",
    Mood.MYSTIC: "神秘的",
    Mood.NATURAL: "自然",
    Mood.NOSTALGIC: "懐かしい",
    Mood.FOCUS: "集中",
    Mood.SLEEP: "睡眠",
    Mood.HOPEFUL: "希望",
}

INSTRUMENT_JA: dict[Instrument, str] = {
    Instrument.PIANO: "ピアノ",
    Instrument.HARP: "ハープ",
    Instrument.MUSIC_BOX: "オルゴール",
    Instrument.ACOUSTIC_GUITAR: "アコースティックギター",
    Instrument.FLUTE: "フルート",
    Instrument.CLARINET: "クラリネット",
    Instrument.MARIMBA: "マリンバ",
    Instrument.SOFT_STRINGS: "柔らかなストリングス",
    Instrument.PAD: "パッド",
    Instrument.BELL: "ベル",
    Instrument.CHIME: "チャイム",
}

NATURE_JA: dict[NatureSound, str] = {
    NatureSound.RAIN: "雨",
    NatureSound.RIVER: "川",
    NatureSound.WAVES: "波",
    NatureSound.FOREST: "森",
    NatureSound.BIRDS: "鳥",
    NatureSound.WIND: "風",
    NatureSound.CAMPFIRE: "焚き火",
}

TEMPO_JA: dict[TempoLevel, str] = {
    TempoLevel.VERY_SLOW: "とてもゆっくり",
    TempoLevel.SLOW: "ゆっくり",
    TempoLevel.GENTLE: "穏やか",
    TempoLevel.NORMAL: "普通",
}
