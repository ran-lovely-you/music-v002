from app.audio.safety_check import run_safety_check
from app.domain.models import AnalysisResult


def _base_analysis(**overrides) -> AnalysisResult:
    base = dict(
        duration_sec=300.0,
        sample_rate=48000,
        peak_dbfs=-8.0,
        rms_dbfs=-22.0,
        lufs_integrated=-18.0,
        clipping_detected=False,
        clipping_sample_count=0,
        high_freq_energy_ratio=0.01,
        low_freq_energy_ratio=0.02,
        max_short_term_dynamic_jump_db=3.0,
        rhythm_intensity=0.05,
        silence_ratio=0.01,
    )
    base.update(overrides)
    return AnalysisResult(**base)


def test_gentle_audio_is_all_green():
    safety = run_safety_check(_base_analysis())
    assert safety.overall_status == "green"
    assert all(item.status == "green" for item in safety.items)


def test_clipping_forces_red_volume_status():
    safety = run_safety_check(_base_analysis(clipping_detected=True, clipping_sample_count=500))
    volume_item = next(i for i in safety.items if i.key == "volume")
    assert volume_item.status == "red"
    assert safety.overall_status == "red"


def test_harsh_high_frequency_flags_red():
    safety = run_safety_check(_base_analysis(high_freq_energy_ratio=0.5))
    item = next(i for i in safety.items if i.key == "high_frequency")
    assert item.status == "red"


def test_heavy_bass_flags_red():
    safety = run_safety_check(_base_analysis(low_freq_energy_ratio=0.3))
    item = next(i for i in safety.items if i.key == "low_frequency")
    assert item.status == "red"


def test_sudden_volume_jump_flags_at_least_yellow():
    safety = run_safety_check(_base_analysis(max_short_term_dynamic_jump_db=8.0))
    item = next(i for i in safety.items if i.key == "volume")
    assert item.status in ("yellow", "red")
