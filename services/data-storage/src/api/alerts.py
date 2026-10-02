from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from storage.local import LocalStorage, SessionLocal
from models import Alert
from api.schemas import AlertAckRequest
router = APIRouter(prefix="/alerts", tags=["alerts"])
storage = LocalStorage()

@router.get("/history")
def get_alerts_history(
    assignment_id: int = Query(...),
    limit: int = Query(50, le=200)
):
    """
    Return alert history for an assignment.
    """
    session: Session = SessionLocal()
    try:
        rows = (
            session.query(Alert)
            .filter(Alert.assignment_id == assignment_id)
            .order_by(Alert.generated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "alert_id": a.alert_id,
                "generated_at": a.generated_at.isoformat(),
                "severity": a.severity,
                "status": a.status,
                "metric": a.metric,
                "value": a.value,
                "description": a.description,
                "full_description": a.full_description,
                "threshold_profile": a.threshold_profile,
            }
            for a in rows
        ]
    finally:
        session.close()

@router.get("/")
def list_alerts():
    items = storage.list_alerts()
    return {"items": items}

@router.post(
    "/{alert_id}/acknowledge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Acknowledge an alert",
)
def acknowledge_alert(
    alert_id: int,
    payload: Optional[AlertAckRequest] = None,
):
    reviewed_by = payload.reviewed_by if payload else None
    clinical_note = payload.clinical_note if payload else None

    updated = storage.acknowledge_alert(
        alert_id=alert_id,
        reviewed_by=reviewed_by,
        clinical_note=clinical_note,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")