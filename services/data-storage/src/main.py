from storage.base import Base
from storage.local import engine
import models  # noqa: F401  (register SQLAlchemy models)

from mqtt_client import start_mqtt
from config_loader import load_health_catalog_config

from api.app import app

import threading
import uvicorn


# ----------------------------
# Database initialization
# ----------------------------
def init_db():
    Base.metadata.create_all(bind=engine)


# ----------------------------
# Main entry point
# ----------------------------
if __name__ == "__main__":
    print("[MAIN] starting data-storage service")

    # Initialize database schema
    init_db()
    print("[MAIN] database initialized")

    #  Load configuration from Health Catalog
    config = load_health_catalog_config()
    print("[MAIN] configuration loaded from Health Catalog")
    # print(config)  # enable only for debugging

    # Start MQTT consumer in background thread
    mqtt_thread = threading.Thread(
        target=start_mqtt,
        args=(config,),
        daemon=True
    )
    mqtt_thread.start()
    print("[MAIN] MQTT consumer started")

    # Start REST API (blocking)
    print("[MAIN] starting REST API on port 8003")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
