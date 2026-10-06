import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path("services/risk_analysis/main.py")

spec = importlib.util.spec_from_file_location("risk_analysis_main", MODULE_PATH)
risk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk)


class FakeMessage:
    topic = "wristbands/9/vitals"

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()


class FakeClient:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, qos=0):
        self.published.append(
            {
                "topic": topic,
                "payload": json.loads(payload),
                "qos": qos,
            }
        )


def test_heart_rate_payload_triggers_critical_cardiac_alert(monkeypatch):
    risk.THRESHOLDS = {
        "profiles": {
            "CARDIAC": {
                "hr": {
                    "NORMAL": [60, 90],
                    "WARNING": [90, 110],
                    "CRITICAL": [110, None],
                },
                "spo2": {
                    "NORMAL": [95, 100],
                    "WARNING": [90, 95],
                    "CRITICAL": [None, 90],
                },
                "temperature": {
                    "NORMAL": [36.0, 37.4],
                    "WARNING": [37.4, 38.2],
                    "CRITICAL": [38.2, None],
                },
                "battery": {
                    "NORMAL": [50, 100],
                    "WARNING": [20, 50],
                    "CRITICAL": [0, 20],
                },
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
        lambda wristband_id: "CARDIAC",
    )

    client = FakeClient()

    risk.on_message(
        client,
        None,
        FakeMessage(
            {
                "wristband_id": 9,
                "measured_at": "2026-10-06T14:39:50Z",
                "heart_rate": 150,
                "spo2": 98,
                "temperature": 36.8,
                "motion": 0.42,
                "battery_level": 80,
            }
        ),
    )

    assert len(client.published) == 1

    event = client.published[0]["payload"]

    assert event["wristband_id"] == 9
    assert event["severity"] == "CRITICAL"
    assert event["threshold_profile"] == "CARDIAC"
    assert event["vital"] == "heart_rate"
    assert event["value"] == 150


def test_battery_level_payload_triggers_critical_alert(monkeypatch):
    risk.THRESHOLDS = {
        "profiles": {
            "STANDARD": {
                "hr": {
                    "NORMAL": [60, 100],
                    "WARNING": [100, 120],
                    "CRITICAL": [120, None],
                },
                "spo2": {
                    "NORMAL": [95, 100],
                    "WARNING": [90, 95],
                    "CRITICAL": [None, 90],
                },
                "temperature": {
                    "NORMAL": [36.0, 37.5],
                    "WARNING": [37.5, 38.5],
                    "CRITICAL": [38.5, None],
                },
                "battery": {
                    "NORMAL": [50, 100],
                    "WARNING": [20, 50],
                    "CRITICAL": [0, 20],
                },
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

    client = FakeClient()

    risk.on_message(
        client,
        None,
        FakeMessage(
            {
                "wristband_id": 9,
                "measured_at": "2026-10-06T14:45:00Z",
                "heart_rate": 75,
                "spo2": 98,
                "temperature": 36.8,
                "motion": 0.42,
                "battery_level": 10,
            }
        ),
    )

    assert len(client.published) == 1

    event = client.published[0]["payload"]

    assert event["severity"] == "CRITICAL"
    assert event["vital"] == "battery_level"
    assert event["value"] == 10
