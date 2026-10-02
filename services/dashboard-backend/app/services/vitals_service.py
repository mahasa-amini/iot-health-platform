from typing import List, Dict
from app.services.storage import Storage


def get_latest_vitals_ui(storage: Storage) -> List[Dict]:
    """
    Return latest vitals for all active patients (UI contract).
    """

    rows = storage.get_latest_vitals()   # ← این الان لیسته

    items: List[Dict] = []

    for row in rows:
        items.append({
            "assignment_id": row["assignment_id"],
            "measured_at": row["measured_at"],
            "heart_rate": row.get("heart_rate"),
            "spo2": row.get("spo2"),
            "temperature": row.get("temperature"),
            "motion": row.get("motion"),
            "battery_level": row.get("battery_level"),
            "wristband_id": row["wristband_id"],
            "patient_name": row.get("patient_name"),
        })

    return items


def get_vitals_history_ui(
    storage: Storage,
    patient_id: int,
    limit: int = 50,
) -> List[Dict]:
    """
    Return vitals history for a patient (UI-ready).
    """

    rows = storage.get_vitals_history(patient_id, limit)

    items: List[Dict] = []

    for row in rows:
        items.append({
            "measured_at": row["measured_at"],
            "heart_rate": row.get("heart_rate"),
            "spo2": row.get("spo2"),
            "temperature": row.get("temperature"),
            "motion": row.get("motion"),
            "battery_level": row.get("battery_level"),
        })

    return items
