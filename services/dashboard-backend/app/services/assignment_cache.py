import os
import requests
from typing import Optional

DATA_STORAGE_URL = os.getenv(
    "DATA_STORAGE_URL",
    "http://data-storage:8003",
)
DATA_STORAGE_BASE = DATA_STORAGE_URL
ASSIGNMENT_ENDPOINT = "/api/v1/assignments/by-wristband/{}"


def get_patient_id_for_wristband(wristband_id: int) -> Optional[int]:
    try:
        resp = requests.get(
            DATA_STORAGE_BASE + ASSIGNMENT_ENDPOINT.format(wristband_id),
            timeout=1.5
        )
        if resp.status_code != 200:
            return None

        patient_id = resp.json().get("patient_id")
        if patient_id is not None:
            return patient_id

    except Exception as e:
        print(f"[ASSIGNMENT] lookup failed for wristband {wristband_id}: {e}")

    return None
