from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "version" in data
