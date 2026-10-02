# tests/test_health_catalog.py

import sys
import re
from pathlib import Path

from fastapi.testclient import TestClient

# ------------------------------------------------------------------
# Make health-catalog service importable for tests
# ------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]   # iot-health-platform
HC_DIR = ROOT / "services" / "health-catalog"

sys.path.insert(0, str(HC_DIR))

from src.main import app  # noqa

client = TestClient(app)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def assert_standard_response(payload: dict):
    """
    Standard response contract:
    {
      "status": "success",
      "data": {...},
      "timestamp": "ISO-8601 string"
    }
    """
    assert isinstance(payload, dict)
    assert payload.get("status") == "success"
    assert "data" in payload
    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], str)
    assert re.match(r"\d{4}-\d{2}-\d{2}", payload["timestamp"])


# ------------------------------------------------------------------
# Sanity / OpenAPI
# ------------------------------------------------------------------

def test_openapi_available():
    res = client.get("/openapi.json")
    assert res.status_code == 200

    data = res.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Health Catalog Service"


# ------------------------------------------------------------------
# GET /thresholds
# ------------------------------------------------------------------

def test_get_thresholds():
    res = client.get("/thresholds")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    data = payload["data"]

    # Your API returns thresholds under "global"
    assert "global" in data
    global_thresholds = data["global"]

    # expected metrics
    assert "hr" in global_thresholds
    assert "spo2" in global_thresholds
    assert "temperature" in global_thresholds

    # expected levels for each metric
    for metric in ["hr", "spo2", "temperature"]:
        assert "normal" in global_thresholds[metric]
        assert "warning" in global_thresholds[metric]
        assert "critical" in global_thresholds[metric]


# ------------------------------------------------------------------
# GET /topics
# ------------------------------------------------------------------

def test_get_topics():
    res = client.get("/topics")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    data = payload["data"]

    assert "mqtt" in data
    mqtt = data["mqtt"]

    assert "base" in mqtt
    assert "subscriptions" in mqtt

    base = mqtt["base"]
    assert "vitals" in base
    assert "alerts" in base
    assert "system" in base


# ------------------------------------------------------------------
# GET /endpoints
# ------------------------------------------------------------------

def test_get_endpoints():
    res = client.get("/endpoints")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    data = payload["data"]
    assert "services" in data

    services = data["services"]
    # Check expected services exist (adjust names if your endpoints.json differs)
    assert "health_catalog" in services
    assert "risk_analysis" in services


# ------------------------------------------------------------------
# GET /patients/{id}
# ------------------------------------------------------------------

def test_get_patient_valid_id():
    res = client.get("/patients/1")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    patient = payload["data"]
    assert patient["patientId"] == 1
    assert "name" in patient
    assert "wristbandId" in patient


def test_get_patient_not_found():
    res = client.get("/patients/999")
    assert res.status_code == 404
    body = res.json()
    assert "detail" in body
