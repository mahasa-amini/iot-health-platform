from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3

from app.models.schemas import WristbandCreateRequest, WristbandCreateResponse
from app.services.container import get_storage
from app.services.storage import Storage
from app.services.wristbands_service import (
    list_wristbands,
    
    create_wristband,
    unassign_wristband,
)
router = APIRouter()


@router.post(
    "/",
    response_model=WristbandCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new wristband",
    description="Register a new wristband device in the system.",
)
def create_wristband_api(
    payload: WristbandCreateRequest,
    db: Storage = Depends(get_storage),
):
    """
    Create wristband endpoint.

    - wristband_id را از UI می‌گیرد
    - داخل جدول WRISTBAND ذخیره می‌کند
    """
    try:
        return create_wristband(db, payload.wristband_id)
    except sqlite3.IntegrityError:
        # Duplicate wristband_id (primary key)
        raise HTTPException(
            status_code=409,
            detail="Wristband ID already exists.",
        )

@router.get(
    "/",
    summary="Get all wristbands",
    description="Return all wristbands registered in the system.",
)
def get_wristbands(db: Storage = Depends(get_storage)):
    return list_wristbands(db)


# @router.get(
#     "/available",
#     summary="Get available wristbands",
#     description="Return wristbands that are not currently assigned to any patient.",
# )
# def get_available_wristbands(db: Storage = Depends(get_storage)):
#     return list_available_wristbands(db)



@router.post("/{wristband_id}/unassign")
def unassign_wristband_api(
    wristband_id: int,
    db: Storage = Depends(get_storage),
):
    try:
        unassign_wristband(db, wristband_id)
        return {"status": "ok"}
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Wristband is not assigned"
        )