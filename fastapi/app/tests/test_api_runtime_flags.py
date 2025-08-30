from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

FASTAPI_DIR = Path(__file__).resolve().parents[1]
if str(FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FASTAPI_DIR))

from app.main import app
from app.db import get_db
from backend.db.models import Base, RuntimeFlag


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_flags.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_runtime_flags_list_initially_empty(client: TestClient):
    r = client.get("/v1/runtime-flags")
    assert r.status_code == 200
    assert r.json() == []


def test_emergency_stop_get_and_toggle(client: TestClient):
    # Initially absent -> treated as disabled
    r0 = client.get("/v1/runtime-flags/emergency-stop")
    assert r0.status_code == 200
    data0 = r0.json()
    assert data0["enabled"] is False

    # Enable
    r1 = client.put("/v1/runtime-flags/emergency-stop", json={"enabled": True})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["enabled"] is True

    # Now list should contain the row
    rlist = client.get("/v1/runtime-flags")
    assert rlist.status_code == 200
    rows = rlist.json()
    assert any(x["key"] == "emergency_stop" and x["value"] == "true" for x in rows)

    # Disable
    r2 = client.put("/v1/runtime-flags/emergency-stop", json={"enabled": False})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["enabled"] is False


def test_generic_set_and_get_flag(client: TestClient):
    # Set a generic flag
    r = client.put("/v1/runtime-flags/sample_flag", json={"value": "on"})
    assert r.status_code == 200
    d = r.json()
    assert d["key"] == "sample_flag"
    assert d["value"] == "on"

    # Retrieve it
    r2 = client.get("/v1/runtime-flags/sample_flag")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["key"] == "sample_flag"
    assert d2["value"] == "on"

