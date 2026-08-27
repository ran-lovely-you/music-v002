from app.domain.models import BgmType, GenerateRequest, Instrument, Mood, NatureSound, TempoLevel
from app.domain.safety import DEFAULT_NEGATIVE_PROMPT_TERMS
from app.prompt.generator import generate_prompt_set


def _sample_request(**overrides) -> GenerateRequest:
    base = dict(
        bgm_type=BgmType.MYSTIC_FOREST,
        moods=[Mood.MYSTIC, Mood.HEALING],
        instruments=[Instrument.HARP, Instrument.PIANO],
        nature_sounds=[NatureSound.FOREST],
        duration_sec=600,
        tempo_level=TempoLevel.SLOW,
    )
    base.update(overrides)
    return GenerateRequest(**base)


def test_generates_three_prompt_variants_and_negative():
    prompts = generate_prompt_set(_sample_request())
    assert prompts.short
    assert prompts.detailed
    assert prompts.professional
    assert prompts.negative
    assert "[ROLE]" in prompts.professional
    assert "harp" in prompts.short.lower() or "harp" in prompts.detailed.lower()


def test_negative_prompt_contains_default_safety_terms():
    prompts = generate_prompt_set(_sample_request())
    for term in DEFAULT_NEGATIVE_PROMPT_TERMS:
        assert term in prompts.negative


def test_falls_back_to_preset_defaults_when_no_selection():
    req = _sample_request(moods=[], instruments=[], nature_sounds=[])
    prompts = generate_prompt_set(req)
    assert prompts.short
    assert prompts.detailed


def test_prompt_never_contains_medical_claims():
    prompts = generate_prompt_set(_sample_request())
    combined = prompts.short + prompts.detailed + prompts.professional
    assert "cure dementia" not in combined.lower()
    assert "認知症" not in combined
