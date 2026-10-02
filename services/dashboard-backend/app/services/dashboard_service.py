from app.services.storage import Storage
from app.models.schemas import DashboardOverviewResponse


def get_dashboard_overview(storage: Storage) -> DashboardOverviewResponse:
    """
    Return aggregated dashboard overview data.

    IMPORTANT:
    - Dashboard Backend does NOT compute anything
    - All aggregation is done in Data Storage Service
    - This function is just orchestration
    """
    return storage.get_dashboard_overview()

