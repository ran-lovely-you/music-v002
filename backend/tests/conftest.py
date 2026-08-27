from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="bgm_test_"))
os.environ.setdefault("DATA_DIR", str(_TEST_DATA_DIR))
os.environ.setdefault("OUTPUT_DIR", str(_TEST_DATA_DIR / "outputs"))
os.environ.setdefault("DB_PATH", str(_TEST_DATA_DIR / "projects.db"))
os.environ.setdefault("ELEVENLABS_API_KEY", "")
os.environ.setdefault("STABILITY_API_KEY", "")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.storage.db import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    init_db()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
