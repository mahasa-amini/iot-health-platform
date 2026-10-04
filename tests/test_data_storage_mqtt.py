import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

from mqtt_client import MQTTClient  # noqa: E402


def test_alert_resolves_wristband_to_active_assignment():
    client = MQTTClient()

    client.storage = MagicMock()
    client._resolve_assignment_id = MagicMock(return_value=6)

    payload = {
        "wristband_id": 9,
        "alert_type": "THRESHOLD_BREACH",
        "severity": "CRITICAL",
        "status": "JUST_GENERATED",
        "threshold_profile": "CARDIAC",
        "metric": "spo2",
        "value": 86,
        "description": "Test alert",
        "full_description": "Test alert for wristband 9",
        "generated_at": "2026-10-04T07:18:57",
    }

    client._handle_alert(payload)

    client._resolve_assignment_id.assert_called_once_with(9)
    client.storage.save_alert.assert_called_once()

    call = client.storage.save_alert.call_args

    assert call.kwargs["assignment_id"] == 6
    assert call.kwargs["data"]["severity"] == "CRITICAL"
    assert call.kwargs["data"]["metric"] == "spo2"
    assert call.kwargs["data"]["value"] == 86
