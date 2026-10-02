from typing import Dict, List, Optional, Union

from app.services.storage import Storage


# ------------------------------------------------------
# Temporary placeholders (until DB + producer is ready)
# ------------------------------------------------------

DEFAULT_METRIC = "Heart Rate"   # موقت: بعداً از DB/producer میاد
DEFAULT_VALUE: Optional[Union[int, float, str]] = "200"  # موقت


def build_full_description(alert: Dict) -> str:
    """
    Build a human-readable full description for an alert.

    ساخت توضیح کامل و قابل فهم برای UI.
    """
    patient_name = alert.get("patient_name", "The patient")
    alert_type = alert.get("alert_type", "an abnormal condition")
    severity = str(alert.get("severity", "WARNING")).lower()

    metric = alert.get("metric", DEFAULT_METRIC)
    value = alert.get("value", DEFAULT_VALUE)

    # If later metric/value become real, this will automatically improve.
    # اگر بعداً metric/value واقعی شوند، همین متن خودکار بهتر می‌شود.
    return (
        f"Patient {patient_name} has a {severity} alert: "
        f"{alert_type}. ({metric} = {value})"
    )


def build_alert_item(alert: Dict) -> Dict:
    """
    Convert a raw alert dict into a UI-ready alert item.

    تبدیل خروجی دیتابیس به خروجی مناسب UI.
    """
    wristband_id = alert.get("wristband_id")

    # Temporary placeholders for metric/value
    # مقدارهای موقت تا زمانی که ستون‌ها/producer آماده شوند
    metric = alert.get("metric") or DEFAULT_METRIC
    value = alert.get("value") if alert.get("value") is not None else DEFAULT_VALUE

    return {
        "alert_id": alert["alert_id"],
        "severity": alert["severity"],
        "status": alert["status"],  # lifecycle را دست نمی‌زنیم
        "alert_type": alert.get("alert_type", "Unknown"),
        "description": alert.get("message", ""),
        "full_description": build_full_description(
            {**alert, "metric": metric, "value": value}
        ),
        "patient_name": alert.get("patient_name"),
        "device_id": f"WB-{wristband_id}" if wristband_id is not None else "UNKNOWN",
        "generated_at": alert.get("generated_at"),
        "metric": metric,
        "value": value,
    }


def list_alerts_ui(storage: Storage) -> List[Dict]:
    """
    Return all alerts for the Alerts page (UI handles filtering/search).

    خروجی لیست هشدارها برای UI (فیلتر در UI انجام می‌شود).
    """
    rows = storage.list_alerts()
    return [build_alert_item(r) for r in rows]


def acknowledge_alert_ui(
    storage: Storage,
    alert_id: int,
    reviewed_by: str | None = None,
    clinical_note: str | None = None,
) -> None:
    """
    Acknowledge an alert from the UI.

    این تابع lifecycle هشدار را به ACKNOWLEDGED تغییر می‌دهد.
    """
    storage.acknowledge_alert(
        alert_id=alert_id,
        reviewed_by=reviewed_by,
        clinical_note=clinical_note,
    )
