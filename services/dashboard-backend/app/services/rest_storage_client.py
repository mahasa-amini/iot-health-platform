import os
import requests
from typing import List, Dict, Optional

from app.services.storage import Storage


DATA_STORAGE_BASE_URL = os.getenv(
    "DATA_STORAGE_URL",
    "http://data-storage:8003/api/v1"
)


class RESTStorageClient(Storage):
    """
    Storage implementation backed by Data Storage Service (REST).
    """

    # ----------------------------
    # Patients
    # ----------------------------
    def get_patients(self) -> List[Dict]:
        resp = requests.get(f"{DATA_STORAGE_BASE_URL}/patients/overview", timeout=5)
        resp.raise_for_status()
        return resp.json()["items"]

    def get_patient_overview(self, patient_id: int) -> Optional[Dict]:
        resp = requests.get(
            f"{DATA_STORAGE_BASE_URL}/patients/{patient_id}/overview",
            timeout=5,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_patient_alerts(self, patient_id: int) -> List[Dict]:
        resp = requests.get(
            f"{DATA_STORAGE_BASE_URL}/patients/{patient_id}/alerts",
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()["items"]

    def create_patient(self, data: dict) -> Dict:
        resp = requests.post(
            f"{DATA_STORAGE_BASE_URL}/patients",
            json=data,
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()

    # ----------------------------
    # Vitals
    # ----------------------------
    def get_latest_vitals(self) -> list[dict]:
        resp = requests.get(
            f"{DATA_STORAGE_BASE_URL}/vitals/latest",
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()["items"]

    def get_vitals_history(
        self,
        patient_id: int,
        limit: int = 50,
    ) -> list[dict]:
        resp = requests.get(
            f"{DATA_STORAGE_BASE_URL}/vitals/history/{patient_id}",
            params={"limit": limit},
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()["items"]

    # ----------------------------
    # Alerts
    # ----------------------------   
    def list_alerts(self) -> list[dict]:
        resp = requests.get(f"{DATA_STORAGE_BASE_URL}/alerts", timeout=5)
        resp.raise_for_status()
        return resp.json()["items"]

    def acknowledge_alert(
        self,
        alert_id: int,
        reviewed_by: Optional[str] = None,
        clinical_note: Optional[str] = None,
    ) -> None:
        Dr = "Dr. Moeini"
        note = "Reviewed and acknowledged."
        if reviewed_by is None:
            reviewed_by = Dr
        if clinical_note is None:
            clinical_note = note
        resp = requests.post(
            f"{DATA_STORAGE_BASE_URL}/alerts/{alert_id}/acknowledge",
            json={
                "reviewed_by": reviewed_by,
                "clinical_note": clinical_note,
            },
            timeout=5,
        )
        resp.raise_for_status()   
    
    # ----------------------------
    # Dashboard overview
    # ----------------------------     
    def get_dashboard_overview(self) -> dict:
        resp = requests.get(
            f"{DATA_STORAGE_BASE_URL}/dashboard/overview",
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    
    # ----------------------------
    # wristbands
    # ----------------------------     
    def list_wristbands(self):
        resp = requests.get(f"{DATA_STORAGE_BASE_URL}/wristbands", timeout=5)
        resp.raise_for_status()
        return resp.json()["items"]

    # def get_available_wristbands(self):
    #     resp = requests.get(
    #         f"{DATA_STORAGE_BASE_URL}/wristbands/available",
    #         timeout=5
    #     )
    #     resp.raise_for_status()
    #     return resp.json()["items"]

    def create_wristband(self, wristband_id: int):
        resp = requests.post(
            f"{DATA_STORAGE_BASE_URL}/wristbands",
            json={"wristband_id": wristband_id},
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def unassign_wristband(self, wristband_id: int) -> None:
        resp = requests.post(
            f"{DATA_STORAGE_BASE_URL}/{wristband_id}/unassign",
            timeout=5,
        )

        if resp.status_code == 404:
            raise ValueError("Wristband not assigned")

        resp.raise_for_status()

    # ----------------------------
    # Unused (for now)
    # ----------------------------
    def count_low_battery_devices(self, threshold: int) -> int:
        raise NotImplementedError


    def assign_wristband(self, patient_id: int, wristband_id: int) -> None:
        raise NotImplementedError
