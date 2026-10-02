from fastapi import APIRouter, Depends

from app.models.schemas import DashboardOverviewResponse
from app.services.dashboard_service import get_dashboard_overview
from app.services.storage import Storage
from app.services.container import get_storage  # ✅ factory واقعی
from app.services.wristbands_service import unassign_wristband
from fastapi import HTTPException

router = APIRouter()


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    summary="Get dashboard overview",
    description="Aggregated metrics and recent alerts for the main dashboard overview page.",
)
def dashboard_overview(db: Storage = Depends(get_storage)):
    """
    Dashboard Overview API endpoint.

    This endpoint:
    - Aggregates system-level KPIs (counts, status summaries)
    - Returns UI-friendly response models
    - Does NOT expose database schema details
    - Uses dependency injection for storage access
    """
    return get_dashboard_overview(db)


