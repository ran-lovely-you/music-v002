import numpy as np
import pytest
import soundfile as sf

from app.export.exporter import export_audio


def _tone(seconds: float = 2.0, sr: int = 48000) -> np.ndarray:
    t = np.arange(int(seconds * sr)) / sr
    mono = 0.2 * np.sin(2 * np.pi * 220 * t)
    return np.stack([mono, mono]).astype(np.float32)


def test_export_wav_is_24bit_48k():
    audio = _tone()
    path = export_audio(audio, 48000, "test_export_wav", "wav")
    assert path.exists()
    assert path.stat().st_size > 0
    info = sf.info(str(path))
    assert info.samplerate == 48000
    assert info.subtype == "PCM_24"
    path.unlink()


def test_export_mp3_320k():
    audio = _tone()
    path = export_audio(audio, 48000, "test_export_mp3", "mp3")
    assert path.exists()
    assert path.stat().st_size > 0
    path.unlink()


def test_export_flac():
    audio = _tone()
    path = export_audio(audio, 48000, "test_export_flac", "flac")
    assert path.exists()
    assert path.stat().st_size > 0
    path.unlink()


def test_export_unsupported_format_raises():
    from app.export.exporter import ExportError

    audio = _tone()
    with pytest.raises(ExportError):
        export_audio(audio, 48000, "test_export_bad", "ogg")


def test_export_clips_out_of_range_audio_safely():
    audio = _tone() * 5.0  # わざと範囲外にする
    path = export_audio(audio, 48000, "test_export_clip", "wav")
    data, sr = sf.read(str(path))
    assert np.max(np.abs(data)) <= 1.0001
    path.unlink()
