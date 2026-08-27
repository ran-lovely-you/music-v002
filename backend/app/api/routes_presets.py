"""GUIの選択肢（プリセット・雰囲気・楽器・自然音・時間・プロバイダー）を返すAPI。"""
from __future__ import annotations

from fastapi import APIRouter

from app.domain.labels import INSTRUMENT_JA, MOOD_JA, NATURE_JA, TEMPO_JA
from app.domain.models import DURATION_CHOICES_SEC, Instrument, Mood, NatureSound, TempoLevel
from app.domain.presets import PRESETS
from app.music_providers.registry import list_providers

router = APIRouter(prefix="/api", tags=["options"])


@router.get("/options")
async def get_options() -> dict:
    return {
        "bgm_types": [
            {
                "key": preset.key.value,
                "label": preset.label_ja,
                "description": preset.description_ja,
                "default_moods": [m.value for m in preset.default_moods],
                "default_instruments": [i.value for i in preset.default_instruments],
                "default_nature_sounds": [n.value for n in preset.default_nature_sounds],
                "default_tempo": preset.default_tempo.value,
            }
            for preset in PRESETS.values()
        ],
        "moods": [{"key": m.value, "label": MOOD_JA[m]} for m in Mood],
        "instruments": [{"key": i.value, "label": INSTRUMENT_JA[i]} for i in Instrument],
        "nature_sounds": [{"key": n.value, "label": NATURE_JA[n]} for n in NatureSound],
        "tempo_levels": [{"key": t.value, "label": TEMPO_JA[t]} for t in TempoLevel],
        "duration_choices_sec": DURATION_CHOICES_SEC,
        "providers": list_providers(),
    }
