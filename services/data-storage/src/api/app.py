from fastapi import FastAPI

from api.assignments import router as assignments_router
from api.vitals import router as vitals_router
from api.alerts import router as alerts_router
from api.patients import router as patients_router
from api.dashboard import router as dashboard_router
from api.wrsitbands import router as wristbands_router


app = FastAPI(
    title="Data Storage API",
    description="REST API for accessing stored vitals, alerts, and assignments",
    version="1.0.0"
)

app.include_router(assignments_router, prefix="/api/v1")
app.include_router(vitals_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(wristbands_router, prefix="/api/v1")

