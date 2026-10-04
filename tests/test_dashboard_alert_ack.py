import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_BACKEND = ROOT / "services" / "dashboard-backend"

sys.path.insert(0, str(DASHBOARD_BACKEND))

from app.services.rest_storage_client import RESTStorageClient  # noqa: E402


def test_acknowledge_alert_preserves_missing_review_metadata(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.rest_storage_client.requests.post",
        fake_post,
    )

    client = RESTStorageClient()
    client.acknowledge_alert(
        alert_id=42,
        reviewed_by=None,
        clinical_note=None,
    )

    assert captured["json"] == {
        "reviewed_by": None,
        "clinical_note": None,
    }
