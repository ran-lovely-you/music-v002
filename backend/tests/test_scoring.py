from app.audio.safety_check import run_safety_check
from app.audio.scoring import compute_score
from app.domain.models import AnalysisResult, BgmType, GenerateRequest, TempoLevel


def _analysis(**overrides) -> AnalysisResult:
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


def _request(**overrides) -> GenerateRequest:
    base = dict(bgm_type=BgmType.DAYTIME_RELAX, duration_sec=300, tempo_level=TempoLevel.GENTLE)
    base.update(overrides)
    return GenerateRequest(**base)


def test_score_within_0_to_100():
    analysis = _analysis()
    safety = run_safety_check(analysis)
    score = compute_score(analysis, safety, _request())
    assert 0.0 <= score.total <= 100.0
    for value in score.breakdown.model_dump().values():
        assert 0.0 <= value <= 100.0


def test_score_has_disclaimer_and_is_not_medical():
    analysis = _analysis()
    safety = run_safety_check(analysis)
    score = compute_score(analysis, safety, _request())
    assert "医学的" in score.disclaimer


def test_clipping_lowers_score():
    good = _analysis()
    bad = _analysis(clipping_detected=True, max_short_term_dynamic_jump_db=20.0)
    req = _request()
    score_good = compute_score(good, run_safety_check(good), req)
    score_bad = compute_score(bad, run_safety_check(bad), req)
    assert score_bad.total < score_good.total


def test_high_bpm_reduces_elderly_fit():
    req_slow = _request(bpm=50)
    req_fast = _request(bpm=100)
    analysis = _analysis()
    safety = run_safety_check(analysis)
    score_slow = compute_score(analysis, safety, req_slow)
    score_fast = compute_score(analysis, safety, req_fast)
    assert score_fast.breakdown.elderly_fit <= score_slow.breakdown.elderly_fit
