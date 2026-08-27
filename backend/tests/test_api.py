from app.domain.models import DURATION_CHOICES_SEC, BgmType, GenerateRequest, TempoLevel


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_options_endpoint_lists_all_choices(client):
    resp = client.get("/api/options")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["bgm_types"]) == 7
    assert len(data["moods"]) == 10
    assert len(data["instruments"]) == 11
    assert len(data["nature_sounds"]) == 7
    assert data["duration_choices_sec"] == DURATION_CHOICES_SEC


def test_prompt_generate_endpoint(client):
    payload = {
        "bgm_type": "forest",
        "moods": ["healing", "natural"],
        "instruments": ["piano", "harp"],
        "nature_sounds": ["river", "birds"],
        "duration_sec": 300,
        "tempo_level": "slow",
    }
    resp = client.post("/api/prompt/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["short"]
    assert data["detailed"]
    assert data["professional"]
    assert data["negative"]


def test_invalid_duration_returns_422(client):
    payload = {"bgm_type": "forest", "duration_sec": 999}
    resp = client.post("/api/prompt/generate", json=payload)
    assert resp.status_code == 422


def test_generate_with_missing_api_key_provider_returns_400(client):
    payload = {"bgm_type": "night", "duration_sec": 300, "provider": "elevenlabs"}
    resp = client.post("/api/bgm/generate", json=payload)
    assert resp.status_code == 400
    assert "APIキー" in resp.json()["detail"]
    # 秘密情報（実際のキー値）が含まれていないことを確認
    assert "sk-" not in resp.json()["detail"]


def test_2_hour_duration_is_accepted_by_model():
    req = GenerateRequest(bgm_type=BgmType.NIGHT_SLEEP, duration_sec=7200, tempo_level=TempoLevel.VERY_SLOW)
    assert req.duration_sec == 7200


def test_full_generation_export_and_project_flow(client):
    payload = {
        "bgm_type": "forest",
        "moods": ["healing", "natural"],
        "instruments": ["piano", "harp"],
        "nature_sounds": ["river", "birds"],
        "duration_sec": 300,
        "tempo_level": "slow",
        "provider": "procedural",
    }
    resp = client.post("/api/bgm/generate", json=payload)
    assert resp.status_code == 200
    result = resp.json()
    generation_id = result["generation_id"]
    assert result["provider_used"] == "procedural"
    assert result["preview_url"].startswith("/outputs/")
    assert result["analysis"]["sample_rate"] == 48000
    assert result["safety"]["overall_status"] in ("green", "yellow", "red")
    assert 0.0 <= result["score"]["total"] <= 100.0

    preview_resp = client.get(result["preview_url"])
    assert preview_resp.status_code == 200

    for fmt, content_type in [("wav", "audio/wav"), ("mp3", "audio/mpeg"), ("flac", "audio/flac")]:
        export_resp = client.post(f"/api/bgm/{generation_id}/export", params={"format": fmt})
        assert export_resp.status_code == 200
        assert export_resp.headers["content-type"] == content_type
        assert len(export_resp.content) > 0

    bad_format_resp = client.post(f"/api/bgm/{generation_id}/export", params={"format": "ogg"})
    assert bad_format_resp.status_code == 400

    save_resp = client.post("/api/projects", json={"generation_id": generation_id, "title": "森のテストBGM"})
    assert save_resp.status_code == 200
    project = save_resp.json()
    assert project["title"] == "森のテストBGM"

    list_resp = client.get("/api/projects")
    assert any(p["id"] == generation_id for p in list_resp.json())

    get_resp = client.get(f"/api/projects/{generation_id}")
    assert get_resp.status_code == 200

    delete_resp = client.delete(f"/api/projects/{generation_id}")
    assert delete_resp.status_code == 200

    missing_resp = client.get(f"/api/projects/{generation_id}")
    assert missing_resp.status_code == 404


def test_export_without_prior_generation_returns_404(client):
    resp = client.post("/api/bgm/does-not-exist/export", params={"format": "wav"})
    assert resp.status_code == 404


def test_youtube_metadata_endpoint(client):
    payload = {"bgm_type": "mystic_forest", "duration_sec": 1800}
    resp = client.post("/api/youtube/metadata", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["titles"]) >= 1
    assert "認知症" not in data["description"]
    assert "予防" not in data["description"]
