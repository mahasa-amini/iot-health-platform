import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

from api.app import app  # noqa: E402
from api import patients  # noqa: E402


client = TestClient(app, raise_server_exceptions=False)


VALID_PATIENT = {
    "name": "Test Patient",
    "age": 40,
    "gender": "OTHER",
    "phone": "123456789",
    "threshold_profile": "STANDARD",
}


def test_create_patient_returns_400_for_domain_validation_error(monkeypatch):
    def fail_create_patient(data):
        raise ValueError("Wristband 1 is already assigned")

    monkeypatch.setattr(
        patients.storage,
        "create_patient",
        fail_create_patient,
    )

    response = client.post(
        "/api/v1/patients",
        json=VALID_PATIENT,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Wristband 1 is already assigned"
    }


def test_create_patient_returns_500_for_unexpected_internal_error(monkeypatch):
    def fail_create_patient(data):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        patients.storage,
        "create_patient",
        fail_create_patient,
    )

    response = client.post(
        "/api/v1/patients",
        json=VALID_PATIENT,
    )

    assert response.status_code == 500
