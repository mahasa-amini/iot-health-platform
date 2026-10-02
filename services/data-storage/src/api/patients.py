from fastapi import APIRouter, HTTPException
from typing import Dict
from api.schemas import PatientCreateRequest
from storage.local import LocalStorage

router = APIRouter(prefix="/patients", tags=["patients"])
 
# ----------------------------------
# Storage instance
# ----------------------------------
storage = LocalStorage()


# ----------------------------------
# GET /patients/overview
# ----------------------------------
@router.get(
    "/overview",
    summary="Get patients overview",
    description="Return patients with active assignment, latest vitals, and latest alert severity.",
)
def get_patients_overview() -> Dict:
    items = storage.get_patients_overview()
    return {"items": items}


# ----------------------------------
# GET /patients/{id}/overview
# ----------------------------------
@router.get(
    "/{patient_id}/overview",
    summary="Get single patient overview",
)
def get_patient_overview(patient_id: int) -> Dict:
    row = storage.get_patient_overview(patient_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return row


# ----------------------------------
# GET /patients/{id}/alerts
# ----------------------------------
@router.get(
    "/{patient_id}/alerts",
    summary="Get patient alerts",
)
def get_patient_alerts(patient_id: int) -> Dict:
    items = storage.get_patient_alerts(patient_id)
    return {"items": items}


# ----------------------------------
# POST /patients
# ----------------------------------
@router.post(
    "",
    summary="Create a new patient",
)
def create_patient(payload: PatientCreateRequest) -> Dict:
    try:
        patient = storage.create_patient(payload.dict())
        return patient
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
