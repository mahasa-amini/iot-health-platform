from fastapi import FastAPI

from .routers.thresholds import router as thresholds_router
from .routers.mqtt import router as mqtt_router
from .routers.services import router as services_router
from .routers.alerts import router as alerts_router
from .routers.environments import router as environments_router

app = FastAPI(
    title="Health Catalog Service",
    description="Central configuration and service registry for IoT Health Platform",
    version="1.0.0"
)

app.include_router(thresholds_router, prefix="/config/thresholds", tags=["Thresholds"])
app.include_router(mqtt_router, prefix="/config/mqtt", tags=["MQTT"])
app.include_router(services_router, prefix="/registry/services", tags=["Services"])
app.include_router(alerts_router, prefix="/config/alerts", tags=["Alerts"])
app.include_router(environments_router, prefix="/config/environments", tags=["Environments"])
