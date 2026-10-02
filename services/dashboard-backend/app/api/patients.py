from fastapi import APIRouter, Depends
from app.models.schemas import PatientCreateRequest, PatientCreateResponse
from app.services.patients_service import create_patient
from app.services.container import get_storage
from app.services.storage import Storage
from app.services.patients_service import get_patients_overview
from fastapi import HTTPException
from app.services.patients_service import get_patient_detail
from app.services.patients_service import get_patient_alerts
router = APIRouter()


@router.get(
    "/",
    summary="Get patients overview",
    description=(
        "Return all patients with their active device (if any), "
        "latest vitals, and risk status computed from latest active alert."
    ),
)
def get_patients(db: Storage = Depends(get_storage)):
    """
    Get patients overview for Patients page.
    """
    return get_patients_overview(db)


@router.get(
    "/{patient_id}/alerts",
    summary="Get alerts for a patient",
    description="Return all alerts related to a specific patient.",
)

def patient_alerts(
    patient_id: int,
    db: Storage = Depends(get_storage),
):
    return get_patient_alerts(db, patient_id)


@router.post(
    "/",
    response_model=PatientCreateResponse,
    summary="Create a new patient",
    description="Create a new patient record in the system.",
)
def create_patient_api(
    payload: PatientCreateRequest,
    db: Storage = Depends(get_storage),
):
    """
    Create patient (and optional wristband assignment).
    Assignment is handled inside Data Storage Service.
    """
    return create_patient(db, payload.dict())


@router.get(
    "/{patient_id}",
    summary="Get patient details",
    description="Return detailed information for a single patient.",
)
def get_patient(
    patient_id: int,
    db: Storage = Depends(get_storage),
):
    try:
        return get_patient_detail(db, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")