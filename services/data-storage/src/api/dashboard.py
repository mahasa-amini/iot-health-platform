from fastapi import APIRouter
from storage.local import LocalStorage

router = APIRouter(tags=["dashboard"])
storage = LocalStorage()


@router.get("/dashboard/overview")
def dashboard_overview():
    return storage.get_dashboard_overview()
    