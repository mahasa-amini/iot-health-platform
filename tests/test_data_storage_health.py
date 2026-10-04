import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

# Use a writable SQLite database for local tests before storage.local is imported.
os.environ["DB_PATH"] = "/tmp/iot-health-data-storage-health-test.db"

from api.app import app  # noqa: E402

client = TestClient(app)


def test_health():
    res = client.get("/health")

    assert res.status_code == 200
    assert res.json() == {
        "status": "healthy",
        "service": "data-storage",
        "database": "connected",
    }


def test_health_returns_503_when_database_is_unavailable(monkeypatch):
    import storage.local

    def fail_connect():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(storage.local.engine, "connect", fail_connect)

    res = client.get("/health")

    assert res.status_code == 503
    assert res.json() == {
        "detail": {
            "status": "unhealthy",
            "service": "data-storage",
            "database": "unavailable",
        }
    }
