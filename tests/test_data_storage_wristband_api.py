import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"
sys.path.insert(0, str(DATA_STORAGE_SRC))

from api.app import app  # noqa: E402
from api import wrsitbands  # noqa: E402


client = TestClient(app, raise_server_exceptions=False)


def test_create_wristband_returns_409_for_duplicate_id(monkeypatch):
    def fail_create_wristband(wristband_id):
        raise IntegrityError(
            "INSERT INTO WRISTBAND",
            {"wristband_id": wristband_id},
            Exception("UNIQUE constraint failed: WRISTBAND.wristband_id"),
        )

    monkeypatch.setattr(
        wrsitbands.storage,
        "create_wristband",
        fail_create_wristband,
    )

    response = client.post(
        "/api/v1/wristbands",
        json={"wristband_id": 1},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Wristband ID already exists."
    }
