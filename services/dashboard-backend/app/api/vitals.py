from fastapi import APIRouter, Depends, Query

from app.services.container import get_storage
from app.services.storage import Storage
from app.services.vitals_service import (
    get_latest_vitals_ui,
    get_vitals_history_ui,
)

router = APIRouter()


@router.get(
    "/latest",
    summary="Get latest vitals for all active patients",
)
def get_latest_vitals(
    db: Storage = Depends(get_storage),
):
    return get_latest_vitals_ui(db)


@router.get(
    "/{patient_id}/history",
    summary="Get vitals history for a patient",
)
def get_vitals_history(
    patient_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Storage = Depends(get_storage),
):
    return get_vitals_history_ui(
        storage=db,
        patient_id=patient_id,
        limit=limit,
    )
