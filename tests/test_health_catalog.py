import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
HC_DIR = ROOT / "services" / "health-catalog"

sys.path.insert(0, str(HC_DIR))

from src.main import app  # noqa: E402

client = TestClient(app)


def assert_standard_response(payload: dict):
    assert isinstance(payload, dict)
    assert payload.get("status") == "success"
    assert "data" in payload
    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], str)
    assert re.match(r"\d{4}-\d{2}-\d{2}", payload["timestamp"])

    parsed_timestamp = datetime.fromisoformat(payload["timestamp"])
    assert parsed_timestamp.tzinfo is not None
    assert parsed_timestamp.utcoffset() == timezone.utc.utcoffset(None)


def test_openapi_available():
    res = client.get("/openapi.json")
    assert res.status_code == 200

    data = res.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Health Catalog Service"


def test_get_thresholds():
    res = client.get("/config/thresholds/")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    data = payload["data"]

    assert data["defaults"]["profile"] == "STANDARD"
    assert "profiles" in data
    assert "STANDARD" in data["profiles"]
    assert "CARDIAC" in data["profiles"]

    for metric in ["hr", "spo2", "temperature", "battery"]:
        assert metric in data["profiles"]["STANDARD"]
        assert "NORMAL" in data["profiles"]["STANDARD"][metric]
        assert "WARNING" in data["profiles"]["STANDARD"][metric]
        assert "CRITICAL" in data["profiles"]["STANDARD"][metric]


def test_get_mqtt_topics():
    res = client.get("/config/mqtt/topics")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    topics = payload["data"]["mqtt_topics"]

    assert topics["vitals"]["subscribe_pattern"] == "wristbands/+/vitals"
    assert topics["risk_events"]["subscribe_pattern"] == "health/risk/+"
    assert topics["alerts"]["topic"] == "health/alerts"


def test_get_services():
    res = client.get("/registry/services/")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    services = payload["data"]["services"]
    names = {service["name"] for service in services}

    assert "health-catalog" in names
    assert "risk-analysis-service" in names
    assert "alert-notification-service" in names
    assert "data-storage-service" in names
    assert "dashboard-backend" in names
    assert "wristband-simulator" in names


def test_get_alert_config():
    res = client.get("/config/alerts/")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    data = payload["data"]

    assert "THRESHOLD_BREACH" in data["alert_types"]
    assert data["lifecycle"]["initial_status"] == "JUST_GENERATED"
    assert "required_fields" in data["payload_contract"]

    required_fields = data["payload_contract"]["required_fields"]
    assert "wristband_id" in required_fields
    assert "assignment_id" not in required_fields


def test_get_environments():
    res = client.get("/config/environments/")
    assert res.status_code == 200

    payload = res.json()
    assert_standard_response(payload)

    data = payload["data"]

    assert data["active_environment"] in data["environments"]
    assert "local" in data["environments"]
    assert "docker" in data["environments"]
    assert data["environments"]["docker"]["mqtt"]["host"] == "mqtt-broker"


def test_health():
    res = client.get("/health")

    assert res.status_code == 200
    assert res.json() == {
        "status": "healthy",
        "service": "health-catalog",
    }
