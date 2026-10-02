from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import patients, vitals, alerts, dashboard, wristbands
from app.mqtt.alert_subscriber import AlertMQTTSubscriber
from app.config.load_health_catalog import load_health_catalog_config
from app.mqtt.vital_subscriber import VitalMQTTSubscriber
from app.api import ws # Ensure WebSocket routes are registered





app = FastAPI(
    title="Dashboard Backend API",
    version="1.0.0",
)

# --------------------------------------------------
# CORS configuration
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # Temporary for testing
    ],
    allow_origin_regex=r"^https://.*\.ngrok.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Routers
# --------------------------------------------------
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(vitals.router, prefix="/vitals", tags=["vitals"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(wristbands.router, prefix="/wristbands", tags=["wristbands"])
app.include_router(ws.router, prefix="/ws", tags=["websockets"])


# --------------------------------------------------
# Startup: load config & start MQTT subscriber
# --------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[DASHBOARD] loading configuration from Health Catalog")

    config = load_health_catalog_config()
    print("[DASHBOARD] configuration loaded from Health Catalog")


    alert_sub = AlertMQTTSubscriber(config)
    alert_sub.start_in_background()
    print("[DASHBOARD] MQTT alert subscriber started")

    vital_sub = VitalMQTTSubscriber(config)
    vital_sub.start_in_background()

    print("[DASHBOARD] MQTT vital subscriber started")


# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/", tags=["health"])
def health_check():
    return {"status": "dashboard-backend running"}
