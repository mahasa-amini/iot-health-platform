from fastapi import APIRouter, Depends, status

from app.models.schemas import AlertAckRequest
from app.services.storage import Storage
from app.services.container import get_storage
from app.services.alerts_service import (
    list_alerts_ui,
    acknowledge_alert_ui,
)

router = APIRouter()


@router.get(
    "/",
    summary="Get all alerts",
    description="Return all alerts for the Alerts page. Filtering is handled in the UI.",
)
def get_alerts(db: Storage = Depends(get_storage)):
    """
    Get all alerts for the Alerts page.

    این endpoint فقط دیتا را برمی‌گرداند
    و هیچ تغییری در وضعیت هشدارها ایجاد نمی‌کند.
    """
    return list_alerts_ui(db)


@router.post(
    "/{alert_id}/acknowledge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Acknowledge an alert",
    description="Mark an alert as acknowledged and optionally attach a clinical note.",
)
def acknowledge_alert(
    alert_id: int,
    payload: AlertAckRequest | None = None,
    db: Storage = Depends(get_storage),
):
    """
    Acknowledge an alert.

    - اگر فرانت body نفرستد → payload = None
    - اگر body خالی {} بفرستد → payload ولی فیلدها None
    - اگر reviewed_by / clinical_note بفرستد → ذخیره می‌شوند
    """

    # --- Safe extraction (prevent NoneType errors) ---
    reviewed_by = payload.reviewed_by if payload else None
    clinical_note = payload.clinical_note if payload else None

    acknowledge_alert_ui(
        storage=db,
        alert_id=alert_id,
        reviewed_by=reviewed_by,
        clinical_note=clinical_note,
    )
