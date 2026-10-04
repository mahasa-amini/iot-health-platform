import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


risk = load_module(
    "risk_analysis_main",
    ROOT / "services" / "risk_analysis" / "main.py",
)

alert = load_module(
    "alert_notification_main",
    ROOT / "services" / "alert_notification" / "main.py",
)


def assert_utc_iso_timestamp(value):
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timezone.utc.utcoffset(None)


def test_risk_event_generated_at_is_utc_aware(monkeypatch):
    risk.THRESHOLDS = {
        "profiles": {
            "STANDARD": {
                "hr": {
                    "CRITICAL": [120, None],
                    "WARNING": [100, 120],
                    "NORMAL": [60, 100],
                }
            }
        }
    }
    risk.MQTT_TOPICS = {
        "mqtt_topics": {
            "risk_events": {
                "template": "health/risk/{wristband_id}"
            }
        }
    }

    monkeypatch.setattr(
        risk,
        "get_profile_for_wristband",
        lambda wristband_id: "STANDARD",
    )

    client = MagicMock()
    msg = SimpleNamespace(
        topic="wristbands/9/vitals",
        payload=json.dumps(
            {
                "wristband_id": 9,
                "hr": 130,
            }
        ).encode(),
    )

    risk.on_message(client, None, msg)

    client.publish.assert_called_once()
    _, payload = client.publish.call_args.args[:2]
    event = json.loads(payload)

    assert_utc_iso_timestamp(event["generated_at"])


def test_alert_generated_at_is_utc_aware():
    alert.ALERT_CONFIG = {
        "lifecycle": {
            "initial_status": "NEW",
        }
    }
    alert.MQTT_TOPICS = {
        "mqtt_topics": {
            "alerts": {
                "topic": "health/alerts",
            }
        }
    }

    client = MagicMock()
    msg = SimpleNamespace(
        topic="health/risk/9",
        payload=json.dumps(
            {
                "wristband_id": 9,
                "alert_type": "THRESHOLD_BREACH",
                "severity": "CRITICAL",
                "threshold_profile": "STANDARD",
                "vital": "hr",
                "value": 130,
            }
        ).encode(),
    )

    alert.on_message(client, None, msg)

    client.publish.assert_called_once()
    _, payload = client.publish.call_args.args[:2]
    event = json.loads(payload)

    assert_utc_iso_timestamp(event["generated_at"])
