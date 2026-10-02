from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from storage.local import SessionLocal, LocalStorage
from models import VitalMeasurement

router = APIRouter(prefix="/vitals", tags=["vitals"])

storage = LocalStorage()


@router.get("/latest")
def get_latest_vitals():
    items = storage.get_latest_vitals()
    return {"items": items}


@router.get("/history/{patient_id}")
def get_vitals_history(
    patient_id: int,
    limit: int = Query(50, ge=1, le=500),
):
    items = storage.get_vitals_history(patient_id, limit)
    return {"items": items}


# @router.get("/history")
# def get_vitals_history(
#     assignment_id: int = Query(...),
#     limit: int = Query(100, le=500)
# ):
#     """
#     Return historical vital measurements for an assignment.
#     """
#     session: Session = SessionLocal()
#     try:
#         rows = (
#             session.query(VitalMeasurement)
#             .filter(VitalMeasurement.assignment_id == assignment_id)
#             .order_by(VitalMeasurement.measured_at.desc())
#             .limit(limit)
#             .all()
#         )

#         return [
#             {
#                 "measured_at": r.measured_at.isoformat(),
#                 "heart_rate": r.heart_rate,
#                 "spo2": r.spo2,
#                 "temperature": r.temperature,
#                 "motion": r.motion,
#                 "battery_level": r.battery_level,
#             }
#             for r in rows
#         ]
#     finally:
#         session.close()
