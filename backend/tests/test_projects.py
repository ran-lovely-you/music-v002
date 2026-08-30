import uuid

from app.audio.safety_check import run_safety_check
from app.audio.scoring import compute_score
from app.domain.models import AnalysisResult, BgmType, GenerateRequest, Instrument, ProjectRecord, TempoLevel
from app.prompt.generator import generate_prompt_set
from app.storage.project_repo import delete_project, get_project, list_projects, save_project, set_favorite


def _sample_record() -> ProjectRecord:
    req = GenerateRequest(
        bgm_type=BgmType.REMINISCENCE,
        instruments=[Instrument.PIANO, Instrument.ACOUSTIC_GUITAR],
        duration_sec=600,
        tempo_level=TempoLevel.SLOW,
    )
    prompts = generate_prompt_set(req)
    analysis = AnalysisResult(
        duration_sec=600.0,
        sample_rate=48000,
        peak_dbfs=-8.0,
        rms_dbfs=-20.0,
        lufs_integrated=-18.0,
        clipping_detected=False,
        clipping_sample_count=0,
        high_freq_energy_ratio=0.01,
        low_freq_energy_ratio=0.02,
        max_short_term_dynamic_jump_db=2.0,
        rhythm_intensity=0.03,
        silence_ratio=0.01,
    )
    safety = run_safety_check(analysis)
    score = compute_score(analysis, safety, req)
    return ProjectRecord(
        id=uuid.uuid4().hex[:12],
        title="テストプロジェクト",
        created_at="2026-01-01T00:00:00",
        bgm_type=req.bgm_type,
        bpm=req.resolved_bpm(),
        instruments=req.instruments,
        nature_sounds=req.nature_sounds,
        prompts=prompts,
        analysis=analysis,
        safety=safety,
        score=score,
        audio_path="/outputs/test.wav",
    )


def test_save_and_get_project_round_trip():
    record = _sample_record()
    save_project(record)
    fetched = get_project(record.id)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.title == record.title
    assert fetched.instruments == record.instruments
    assert fetched.score.total == record.score.total
    delete_project(record.id)


def test_list_projects_includes_saved_project():
    record = _sample_record()
    save_project(record)
    all_projects = list_projects()
    assert any(p.id == record.id for p in all_projects)
    delete_project(record.id)


def test_delete_project_removes_it():
    record = _sample_record()
    save_project(record)
    assert delete_project(record.id) is True
    assert get_project(record.id) is None


def test_get_missing_project_returns_none():
    assert get_project("does-not-exist") is None


def test_set_favorite_toggles_flag():
    record = _sample_record()
    save_project(record)
    updated = set_favorite(record.id, True)
    assert updated is not None
    assert updated.is_favorite is True
    fetched = get_project(record.id)
    assert fetched is not None
    assert fetched.is_favorite is True
    delete_project(record.id)


def test_set_favorite_missing_project_returns_none():
    assert set_favorite("does-not-exist", True) is None


def test_list_projects_filters_by_profile():
    record = _sample_record()
    record.profile_id = "fam-1"
    record.profile_name = "おばあちゃん"
    save_project(record)
    matching = list_projects(profile_id="fam-1")
    other = list_projects(profile_id="fam-2")
    assert any(p.id == record.id for p in matching)
    assert not any(p.id == record.id for p in other)
    delete_project(record.id)
