from typing import Dict, List, Optional

from app.services.storage import Storage


# --------------------------------------------------
# Constants / Enums (UI-facing)
# --------------------------------------------------

RISK_NORMAL = "NORMAL"
RISK_WARNING = "WARNING"
RISK_CRITICAL = "CRITICAL"


# --------------------------------------------------
# Patients overview
# --------------------------------------------------

def get_patients_overview(storage: Storage) -> Dict:
    """
    Build UI-ready patients list for Patients page.
    """

    rows = storage.get_patients()

    items: List[Dict] = []

    for row in rows:
        wristband_id = row.get("wristband_id")
        latest_alert_severity = row.get("latest_alert_severity")

        risk_status = _compute_risk_status(latest_alert_severity)
        has_active_alert = latest_alert_severity is not None

        items.append({
            # -------------------------
            # Patient identity
            # -------------------------
            "patient_id": row["patient_id"],
            "name": row["patient_name"],
            "age": row.get("age"),
            "gender": row.get("gender"),
            "phone": row.get("phone"),

            # -------------------------
            # Device info
            # -------------------------
            "device_id": _map_wristband_to_device_id(wristband_id),
            "device_status": "ACTIVE" if wristband_id else "INACTIVE",

            # -------------------------
            # Latest vitals (optional)
            # -------------------------
            "vitals": {
                "heart_rate": row.get("heart_rate"),
                "spo2": row.get("spo2"),
                "temperature": row.get("temperature"),
                "battery_level": row.get("battery_level"),
            } if wristband_id else None,

            # -------------------------
            # Status & metadata
            # -------------------------
            "risk_status": risk_status,
            "has_active_alert": has_active_alert,
            "last_update": row.get("last_update"),
        })

    return {"items": items}


# --------------------------------------------------
# Patient alerts
# --------------------------------------------------

def get_patient_alerts(storage: Storage, patient_id: int) -> Dict:
    """
    Build UI-ready alerts list for a single patient.
    """
    rows = storage.get_patient_alerts(patient_id)
    items: List[Dict] = []

    for row in rows:
        wristband_id = row.get("wristband_id")

        items.append({
            "alert_id": row["alert_id"],
            "assignment_id": row["assignment_id"],
            "generated_at": row["generated_at"],

            # Alert content
            "severity": row["severity"],
            "status": row["status"],
            "alert_type": row["alert_type"],
            "threshold_profile": row.get("threshold_profile"),

            "description": row.get("description"),
            "full_description": row.get("full_description"),

            "metric": row.get("metric"),
            "value": row.get("value"),

            # Device
            "device_id": _map_wristband_to_device_id(wristband_id),
        })

    return {"items": items}


# --------------------------------------------------
# Create / Update
# --------------------------------------------------

def create_patient(storage: Storage, payload: dict) -> dict:
    """
    Create patient (and optional wristband assignment).

    Assignment is handled inside Data Storage Service.
    """
    return storage.create_patient(payload)



def get_patient_detail(storage: Storage, patient_id: int) -> dict:
    """
    Build UI-ready patient detail response.
    """
    row = storage.get_patient_overview(patient_id)

    if row is None:
        raise ValueError("Patient not found")

    wristband_id = row.get("wristband_id")
    latest_alert_severity = row.get("latest_alert_severity")

    risk_status = _compute_risk_status(latest_alert_severity)

    return {
        "patient_id": row["patient_id"],
        "name": row["patient_name"],
        "age": row.get("age"),
        "gender": row.get("gender"),
        "phone": row.get("phone"),

        "device_id": _map_wristband_to_device_id(wristband_id),
        "device_status": "ACTIVE" if wristband_id else "INACTIVE",

        "vitals": {
            "heart_rate": row.get("heart_rate"),
            "spo2": row.get("spo2"),
            "temperature": row.get("temperature"),
            "battery_level": row.get("battery_level"),
        } if wristband_id else None,

        "risk_status": risk_status,
        "has_active_alert": latest_alert_severity is not None,
        "last_update": row.get("last_update"),
    }



# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def _map_wristband_to_device_id(wristband_id: Optional[int]) -> Optional[str]:
    """
    Convert internal wristband_id to UI-friendly device_id.
    """
    if wristband_id is None:
        return None
    return f"WB-{wristband_id}"


def _compute_risk_status(latest_alert_severity: Optional[str]) -> str:
    """
    Compute patient risk status based on latest active alert severity.
    """
    if latest_alert_severity == RISK_CRITICAL:
        return RISK_CRITICAL

    if latest_alert_severity == RISK_WARNING:
        return RISK_WARNING

    return RISK_NORMAL

