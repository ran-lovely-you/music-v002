import uuid

from app.domain.models import Profile
from app.storage.profile_repo import create_profile, delete_profile, get_profile, list_profiles


def _sample_profile() -> Profile:
    return Profile(
        id=uuid.uuid4().hex[:12],
        name="おばあちゃん",
        emoji="👵",
        created_at="2026-01-01T00:00:00",
    )


def test_create_and_get_profile():
    profile = _sample_profile()
    create_profile(profile)
    fetched = get_profile(profile.id)
    assert fetched is not None
    assert fetched.name == profile.name
    assert fetched.emoji == profile.emoji
    delete_profile(profile.id)


def test_list_profiles_includes_created_profile():
    profile = _sample_profile()
    create_profile(profile)
    assert any(p.id == profile.id for p in list_profiles())
    delete_profile(profile.id)


def test_delete_profile_removes_it():
    profile = _sample_profile()
    create_profile(profile)
    assert delete_profile(profile.id) is True
    assert get_profile(profile.id) is None


def test_get_missing_profile_returns_none():
    assert get_profile("does-not-exist") is None
