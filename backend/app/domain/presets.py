"""BGMタイプ（プリセット）定義。

STEP: 4 のプリセット定義（Aの朝の目覚め〜Gの神秘的な森）。
特定の既存曲を模倣する指示は含めない。あくまでムード・楽器・自然音の組み合わせのみを扱う。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import BgmType, Instrument, Mood, NatureSound, TempoLevel


@dataclass(frozen=True)
class BgmPreset:
    key: BgmType
    label_ja: str
    description_ja: str
    default_moods: list[Mood]
    default_instruments: list[Instrument]
    default_nature_sounds: list[NatureSound]
    default_tempo: TempoLevel
    scale_mode: str  # "major" | "minor" | "pentatonic_major" | "pentatonic_minor"
    theme_keywords_en: list[str] = field(default_factory=list)


PRESETS: dict[BgmType, BgmPreset] = {
    BgmType.MORNING: BgmPreset(
        key=BgmType.MORNING,
        label_ja="朝の目覚め",
        description_ja="明るく穏やかで爽やかな、前向きな気持ちを支える朝のBGM",
        default_moods=[Mood.BRIGHT, Mood.HOPEFUL, Mood.CALM],
        default_instruments=[Instrument.PIANO, Instrument.ACOUSTIC_GUITAR, Instrument.FLUTE],
        default_nature_sounds=[NatureSound.BIRDS],
        default_tempo=TempoLevel.GENTLE,
        scale_mode="pentatonic_major",
        theme_keywords_en=["gentle morning light", "fresh air", "hopeful new day", "soft sunrise"],
    ),
    BgmType.DAYTIME_RELAX: BgmPreset(
        key=BgmType.DAYTIME_RELAX,
        label_ja="昼間のリラックス",
        description_ja="穏やかなピアノやハープ、柔らかなパッドで過ごす日中のくつろぎ時間",
        default_moods=[Mood.CALM, Mood.HEALING],
        default_instruments=[Instrument.PIANO, Instrument.HARP, Instrument.SOFT_STRINGS, Instrument.PAD],
        default_nature_sounds=[],
        default_tempo=TempoLevel.GENTLE,
        scale_mode="major",
        theme_keywords_en=["gentle daytime relaxation", "soft afternoon calm", "comfortable living room"],
    ),
    BgmType.FOCUS: BgmPreset(
        key=BgmType.FOCUS,
        label_ja="集中・軽い認知活動",
        description_ja="安定したリズムと控えめなメロディで、軽い認知活動の時間に流しやすいBGM",
        default_moods=[Mood.FOCUS, Mood.CALM],
        default_instruments=[Instrument.PIANO, Instrument.MARIMBA],
        default_nature_sounds=[],
        default_tempo=TempoLevel.NORMAL,
        scale_mode="major",
        theme_keywords_en=["steady gentle rhythm", "calm focus", "unobtrusive melody", "light cognitive activity"],
    ),
    BgmType.REMINISCENCE: BgmPreset(
        key=BgmType.REMINISCENCE,
        label_ja="回想・思い出",
        description_ja="懐かしさを感じやすい、ピアノ・アコースティックギター・オルゴールのあたたかな音色",
        default_moods=[Mood.NOSTALGIC, Mood.CALM],
        default_instruments=[Instrument.PIANO, Instrument.ACOUSTIC_GUITAR, Instrument.MUSIC_BOX, Instrument.SOFT_STRINGS],
        default_nature_sounds=[],
        default_tempo=TempoLevel.SLOW,
        scale_mode="major",
        theme_keywords_en=["warm nostalgic memories", "gentle reminiscence", "tender bittersweet warmth"],
    ),
    BgmType.FOREST_NATURE: BgmPreset(
        key=BgmType.FOREST_NATURE,
        label_ja="森・自然",
        description_ja="森林・小川・小鳥・そよ風とハープやピアノが溶け合うアンビエントBGM",
        default_moods=[Mood.NATURAL, Mood.HEALING],
        default_instruments=[Instrument.HARP, Instrument.PIANO, Instrument.PAD],
        default_nature_sounds=[NatureSound.FOREST, NatureSound.RIVER, NatureSound.BIRDS, NatureSound.WIND],
        default_tempo=TempoLevel.SLOW,
        scale_mode="pentatonic_major",
        theme_keywords_en=["deep peaceful forest", "gentle stream", "birdsong", "soft breeze", "ambient nature"],
    ),
    BgmType.NIGHT_SLEEP: BgmPreset(
        key=BgmType.NIGHT_SLEEP,
        label_ja="夜・睡眠前",
        description_ja="非常に穏やかでゆっくり、音数を減らし急激な変化を避けた就寝前BGM",
        default_moods=[Mood.SLEEP, Mood.CALM],
        default_instruments=[Instrument.PIANO, Instrument.PAD],
        default_nature_sounds=[NatureSound.RAIN],
        default_tempo=TempoLevel.VERY_SLOW,
        scale_mode="minor",
        theme_keywords_en=["very gentle bedtime calm", "slow soft ambient", "minimal notes", "quiet night"],
    ),
    BgmType.MYSTIC_FOREST: BgmPreset(
        key=BgmType.MYSTIC_FOREST,
        label_ja="神秘的な森",
        description_ja="神秘的な森・優しい精霊・光と水と木々をイメージした穏やかな魔法のようなヒーリングBGM",
        default_moods=[Mood.MYSTIC, Mood.HEALING, Mood.HOPEFUL],
        default_instruments=[Instrument.HARP, Instrument.BELL, Instrument.CHIME, Instrument.PAD, Instrument.FLUTE],
        default_nature_sounds=[NatureSound.FOREST, NatureSound.WIND],
        default_tempo=TempoLevel.SLOW,
        scale_mode="pentatonic_minor",
        theme_keywords_en=[
            "mystical enchanted forest",
            "gentle forest spirits",
            "guardian of the woods",
            "soft glowing light",
            "sparkling water",
            "ancient trees",
            "calm gentle magic",
        ],
    ),
}


def get_preset(bgm_type: BgmType) -> BgmPreset:
    return PRESETS[bgm_type]
