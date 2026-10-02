import requests
from typing import Dict, Optional

DATA_STORAGE_BASE = "http://data-storage:8003"
ASSIGNMENT_ENDPOINT = "/api/v1/assignments/by-wristband/{}"

_assignment_cache: Dict[int, int] = {}


def get_patient_id_for_wristband(wristband_id: int) -> Optional[int]:
    if wristband_id in _assignment_cache:
        return _assignment_cache[wristband_id]

    try:
        resp = requests.get(
            DATA_STORAGE_BASE + ASSIGNMENT_ENDPOINT.format(wristband_id),
            timeout=1.5
        )
        if resp.status_code != 200:
            return None

        patient_id = resp.json().get("patient_id")
        if patient_id is not None:
            _assignment_cache[wristband_id] = patient_id
            return patient_id

    except Exception as e:
        print(f"[ASSIGNMENT] lookup failed for wristband {wristband_id}: {e}")

    return None
