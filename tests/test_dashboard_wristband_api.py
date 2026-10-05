import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_BACKEND = ROOT / "services" / "dashboard-backend"
sys.path.insert(0, str(DASHBOARD_BACKEND))

from app.api import wristbands  # noqa: E402
from app.services.container import get_storage  # noqa: E402
from app.services.rest_storage_client import RESTStorageClient  # noqa: E402


class DuplicateWristbandStorage:
    def create_wristband(self, wristband_id):
        raise ValueError("Wristband ID already exists.")


app = FastAPI()
app.include_router(
    wristbands.router,
    prefix="/wristbands",
)
app.dependency_overrides[get_storage] = lambda: DuplicateWristbandStorage()

client = TestClient(app, raise_server_exceptions=False)


def test_create_wristband_returns_409_for_duplicate_id():
    response = client.post(
        "/wristbands/",
        json={"wristband_id": 1},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Wristband ID already exists."
    }


def test_rest_storage_translates_upstream_409_to_value_error(monkeypatch):
    class FakeResponse:
        status_code = 409

        def raise_for_status(self):
            raise AssertionError(
                "Known 409 conflict should be translated before raise_for_status"
            )

        def json(self):
            return {"detail": "Wristband ID already exists."}

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.rest_storage_client.requests.post",
        fake_post,
    )

    storage = RESTStorageClient()

    with pytest.raises(
        ValueError,
        match="Wristband ID already exists",
    ):
        storage.create_wristband(1)
