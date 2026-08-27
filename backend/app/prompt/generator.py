"""AIプロンプト自動生成機能（STEP 4 / 6-7）。

ユーザーが選んだBGMタイプ・雰囲気・楽器・自然音・時間・BPMから、
Short / Detailed / Professional の3種類の英語プロンプトと
Negative Prompt を自動生成する。
"""
from __future__ import annotations

from app.domain.models import GenerateRequest, Instrument, Mood, NatureSound, PromptSet
from app.domain.presets import get_preset
from app.domain.safety import build_negative_prompt

INSTRUMENT_EN: dict[Instrument, str] = {
    Instrument.PIANO: "gentle soft piano",
    Instrument.HARP: "warm harp",
    Instrument.MUSIC_BOX: "delicate music box",
    Instrument.ACOUSTIC_GUITAR: "soft acoustic guitar",
    Instrument.FLUTE: "breathy flute",
    Instrument.CLARINET: "warm clarinet",
    Instrument.MARIMBA: "soft marimba",
    Instrument.SOFT_STRINGS: "soft strings",
    Instrument.PAD: "warm ambient pad",
    Instrument.BELL: "gentle bell",
    Instrument.CHIME: "soft wind chime",
}

MOOD_EN: dict[Mood, str] = {
    Mood.HEALING: "healing",
    Mood.CALM: "calm",
    Mood.BRIGHT: "bright",
    Mood.REASSURING: "reassuring",
    Mood.MYSTIC: "mystical",
    Mood.NATURAL: "natural",
    Mood.NOSTALGIC: "nostalgic",
    Mood.FOCUS: "focused",
    Mood.SLEEP: "sleepy",
    Mood.HOPEFUL: "hopeful",
}

NATURE_EN: dict[NatureSound, str] = {
    NatureSound.RAIN: "gentle rain",
    NatureSound.RIVER: "soft flowing river",
    NatureSound.WAVES: "calm ocean waves",
    NatureSound.FOREST: "quiet forest ambience",
    NatureSound.BIRDS: "distant soft birdsong",
    NatureSound.WIND: "gentle breeze",
    NatureSound.CAMPFIRE: "soft crackling campfire",
}


def _join(items: list[str]) -> str:
    return ", ".join(items)


def generate_prompt_set(req: GenerateRequest) -> PromptSet:
    preset = get_preset(req.bgm_type)

    moods = req.moods or preset.default_moods
    instruments = req.instruments or preset.default_instruments
    nature = req.nature_sounds or preset.default_nature_sounds
    bpm = req.resolved_bpm()
    minutes = req.duration_sec // 60

    mood_words = [MOOD_EN.get(m, m.value) for m in moods]
    instrument_words = [INSTRUMENT_EN.get(i, i.value) for i in instruments]
    nature_words = [NATURE_EN.get(n, n.value) for n in nature]

    # --- Short Prompt ---
    short_parts = [
        f"{_join(mood_words)} instrumental BGM for elderly listeners",
        preset.label_ja and preset.theme_keywords_en[0] if preset.theme_keywords_en else "",
        _join(instrument_words),
    ]
    short_prompt = ", ".join(p for p in short_parts if p)

    # --- Detailed Prompt ---
    detail_lines = [
        f"An original {_join(mood_words)} instrumental background music track designed for elderly listeners.",
        f"Theme: {preset.description_ja} ({_join(preset.theme_keywords_en)}).",
        f"Instrumentation: {_join(instrument_words) if instrument_words else 'soft solo piano'}.",
    ]
    if nature_words:
        detail_lines.append(f"Layered nature ambience: {_join(nature_words)}, mixed subtly under the music.")
    detail_lines.append(
        f"Tempo: very slow and steady around {bpm} BPM, no sudden tempo or dynamic changes."
    )
    detail_lines.append(
        "Smooth natural fade-in and fade-out, gentle dynamics, no sudden loud accents, "
        "warm balanced tone, comfortable for long uninterrupted listening, safe for repeated/looped playback."
    )
    detail_lines.append(f"Approximate duration: {minutes} minutes.")
    detailed_prompt = " ".join(detail_lines)

    # --- Professional Prompt ---
    prof_lines = [
        "[ROLE] You are composing original instrumental background music for elderly care use "
        "(homes, day-care centers, rehabilitation, and bedtime relaxation).",
        f"[GENRE/MOOD] {_join(mood_words)}, {preset.label_ja} theme.",
        f"[INSTRUMENTATION] {_join(instrument_words) if instrument_words else 'solo soft piano'}"
        + (f" with ambient nature layers: {_join(nature_words)}" if nature_words else "") + ".",
        f"[TEMPO] {bpm} BPM, gentle and unwavering, no abrupt tempo shifts.",
        "[DYNAMICS] Narrow dynamic range, gentle compression feel, no sudden volume spikes, "
        "no harsh high frequencies, no excessive low-end bass, no aggressive percussion.",
        "[STRUCTURE] Smooth intro fade-in, sustained gentle development, smooth outro fade-out, "
        "seamless loop-friendly structure suitable for very long continuous playback.",
        f"[DURATION] {minutes} minutes.",
        "[PURPOSE] Cognitive-support ambience, relaxation, calm focus, and comfortable listening "
        "for elderly audiences; must remain pleasant on repeated or extended listening.",
        "[ORIGINALITY] Fully original composition, not an imitation or reproduction of any existing copyrighted song.",
    ]
    professional_prompt = "\n".join(prof_lines)

    negative_prompt = build_negative_prompt()

    return PromptSet(
        short=short_prompt,
        detailed=detailed_prompt,
        professional=professional_prompt,
        negative=negative_prompt,
    )
