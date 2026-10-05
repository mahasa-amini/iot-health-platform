import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_BACKEND = ROOT / "services" / "dashboard-backend"
sys.path.insert(0, str(DASHBOARD_BACKEND))

from app.api import patients  # noqa: E402
from app.services.container import get_storage  # noqa: E402
from app.services.rest_storage_client import RESTStorageClient  # noqa: E402


VALID_PATIENT = {
    "name": "Test Patient",
    "age": 40,
    "gender": "OTHER",
    "phone": "123456789",
    "threshold_profile": "STANDARD",
    "wristband_id": 1,
}


class ConflictingPatientStorage:
    def create_patient(self, data):
        raise ValueError("Wristband 1 is already assigned")


app = FastAPI()
app.include_router(
    patients.router,
    prefix="/patients",
)
app.dependency_overrides[get_storage] = lambda: ConflictingPatientStorage()

client = TestClient(app, raise_server_exceptions=False)


def test_create_patient_preserves_domain_error_as_400():
    response = client.post(
        "/patients/",
        json=VALID_PATIENT,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Wristband 1 is already assigned"
    }


def test_rest_storage_translates_upstream_400_to_value_error(monkeypatch):
    class FakeResponse:
        status_code = 400

        def raise_for_status(self):
            raise AssertionError(
                "Known 400 domain error should be translated before raise_for_status"
            )

        def json(self):
            return {
                "detail": "Wristband 1 is already assigned"
            }

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.rest_storage_client.requests.post",
        fake_post,
    )

    storage = RESTStorageClient()

    with pytest.raises(
        ValueError,
        match="Wristband 1 is already assigned",
    ):
        storage.create_patient(VALID_PATIENT)
