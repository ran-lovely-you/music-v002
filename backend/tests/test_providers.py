import numpy as np
import pytest

from app.domain.models import BgmType, GenerateRequest, Instrument, TempoLevel
from app.music_providers.base import ProviderError
from app.music_providers.registry import get_provider, list_providers


def _short_request() -> GenerateRequest:
    return GenerateRequest(
        bgm_type=BgmType.FOCUS,
        instruments=[Instrument.PIANO],
        duration_sec=300,
        tempo_level=TempoLevel.NORMAL,
    )


def test_procedural_provider_available_without_api_key():
    provider = get_provider("procedural")
    assert provider.name == "procedural"
    assert provider.requires_api_key is False


@pytest.mark.asyncio
async def test_procedural_provider_generates_correct_shape():
    provider = get_provider("procedural")
    audio, sr = await provider.generate(_short_request(), "prompt text", "negative text", seed=7)
    assert sr == 48000
    assert audio.ndim == 2
    assert audio.shape[0] == 2
    assert audio.shape[1] == pytest.approx(300 * 48000, rel=0.01)
    assert not np.isnan(audio).any()
    assert np.max(np.abs(audio)) <= 1.0001


def test_elevenlabs_provider_requires_api_key():
    with pytest.raises(ProviderError):
        get_provider("elevenlabs")


def test_stability_provider_requires_api_key():
    with pytest.raises(ProviderError):
        get_provider("stability")


def test_unknown_provider_raises_error():
    with pytest.raises(ProviderError):
        get_provider("does-not-exist")


def test_list_providers_reports_availability():
    providers = list_providers()
    keys = {p["key"] for p in providers}
    assert {"procedural", "elevenlabs", "stability"} <= keys
    procedural = next(p for p in providers if p["key"] == "procedural")
    assert procedural["available"] is True
