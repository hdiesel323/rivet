from __future__ import annotations

import pytest


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "rivet.sqlite"
    monkeypatch.setenv("RIVET_DB_PATH", str(path))
    monkeypatch.setenv("RIVET_DEMO", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LOCAL_BASE_URL", raising=False)
    monkeypatch.delenv("JEV_URL", raising=False)
    monkeypatch.delenv("RIVET_API_KEY", raising=False)
    from core.ledger import init_db

    init_db(str(path))
    return path
