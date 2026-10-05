import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

from api.app import app  # noqa: E402

client = TestClient(app)


def test_health(monkeypatch):
    import storage.local

    connection = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = connection
    context_manager.__exit__.return_value = False

    monkeypatch.setattr(
        storage.local.engine,
        "connect",
        MagicMock(return_value=context_manager),
    )

    res = client.get("/health")

    assert res.status_code == 200
    assert res.json() == {
        "status": "healthy",
        "service": "data-storage",
        "database": "connected",
    }
    connection.execute.assert_called_once()


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
