from fastapi import APIRouter, HTTPException
from storage.local import LocalStorage
from api.schemas import WristbandCreateRequest

router = APIRouter(tags=["wristbands"])
storage = LocalStorage()


@router.get("/wristbands")
def get_wristbands():
    return {"items": storage.list_wristbands()}


@router.get("/wristbands/available")
def get_available_wristbands():
    return {"items": storage.list_available_wristbands()}


@router.post("/wristbands")
def create_wristband(payload: WristbandCreateRequest):
    return storage.create_wristband(payload.wristband_id)

@router.post("/{wristband_id}/unassign")
def unassign_wristband(wristband_id: int):
    success = storage.unassign_wristband(wristband_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="No active assignment for this wristband"
        )

    return {"status": "unassigned"}
