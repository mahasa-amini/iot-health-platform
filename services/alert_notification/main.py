import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
import time

# ----------------------------------
# Health Catalog endpoints
# ----------------------------------
HEALTH_CATALOG_URL = "http://health-catalog:8000"

MQTT_TOPICS_ENDPOINT = "/config/mqtt/topics"
ALERTS_ENDPOINT = "/config/alerts"
ENVIRONMENTS_ENDPOINT = "/config/environments"


# ----------------------------------
# Global configs (loaded at startup)
# ----------------------------------
MQTT_TOPICS = {}
ALERT_CONFIG = {}
ENV_CONFIG = {}


# ----------------------------------
# Helpers
# ----------------------------------
def load_from_catalog(endpoint: str, retries: int = 5, delay: float = 2.0) -> dict:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(
                f"[ALERT][CONFIG] Loading {endpoint} "
                f"(attempt {attempt}/{retries})"
            )

            response = requests.get(
                f"{HEALTH_CATALOG_URL}{endpoint}",
                timeout=5
            )
            response.raise_for_status()
            return response.json()["data"]

        except Exception as e:
            last_error = e
            print(
                f"[ALERT][WARN] Health Catalog not ready "
                f"for {endpoint}: {e}"
            )
            time.sleep(delay)

    raise RuntimeError(
        f"Failed to load {endpoint} after {retries} attempts: {last_error}"
    )


def build_descriptions(event: dict):
    """
    Build short and full descriptions for UI
    """
    metric = event.get("vital")
    value = event.get("value")
    severity = event.get("severity")
    wristband_id = event.get("wristband_id")

    metric_label = metric.replace("_", " ").title()

    short_description = f"{metric_label} above {severity} threshold"

    full_description = (
        f"The {metric_label.lower()} recorded from wristband "
        f"WB-{wristband_id} was {value}, which exceeds the "
        f"{severity} threshold and may require immediate medical attention."
    )

    return short_description, full_description


# ----------------------------------
# MQTT callbacks
# ----------------------------------
def on_connect(client, userdata, flags, rc):
    print(f"[ALERT] Connected to MQTT broker (rc={rc})")

    risk_topic = MQTT_TOPICS["mqtt_topics"]["risk_events"]["subscribe_pattern"]
    client.subscribe(risk_topic, qos=1)

    print(f"[ALERT] Subscribed to {risk_topic}")


def on_message(client, userdata, msg):
    print(f"[ALERT] Risk event received on {msg.topic}")

    try:
        event = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("[ALERT] Invalid JSON payload")
        return

    # Build UI-friendly descriptions
    short_desc, full_desc = build_descriptions(event)

    # Final alert payload (UI + Storage ready)
    alert = {
        "assignment_id": event.get("wristband_id"),  # DB will resolve mapping
        "alert_type": event.get("alert_type"),
        "severity": event.get("severity"),
        "status": ALERT_CONFIG["lifecycle"]["initial_status"],

        "metric": event.get("vital"),
        "value": event.get("value"),

        "description": short_desc,
        "full_description": full_desc,

        "threshold_profile": event.get("threshold_profile"),
        "generated_at": datetime.utcnow().isoformat()
    }

    alert_topic = MQTT_TOPICS["mqtt_topics"]["alerts"]["topic"]

    client.publish(alert_topic, json.dumps(alert), qos=1)

    print(f"[ALERT] Final alert published: {alert}")


# ----------------------------------
# Main
# ----------------------------------
def main():
    global MQTT_TOPICS, ALERT_CONFIG, ENV_CONFIG

    print("[ALERT] Alert Notification Service starting")

    # Load configs from Health Catalog
    MQTT_TOPICS = load_from_catalog(MQTT_TOPICS_ENDPOINT)
    print(f"[ALERT] MQTT Topics loaded")
    ALERT_CONFIG = load_from_catalog(ALERTS_ENDPOINT)
    print(f"[ALERT] Alert Config loaded")
    ENV_CONFIG = load_from_catalog(ENVIRONMENTS_ENDPOINT)
    print(f"[ALERT] Environment Config loaded")

    # Resolve active environment
    active_env = ENV_CONFIG["active_environment"]
    mqtt_conf = ENV_CONFIG["environments"][active_env]["mqtt"]

    # MQTT client
    client = mqtt.Client(client_id="alert-notification-service")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[ALERT] Connecting to MQTT {mqtt_conf['host']}:{mqtt_conf['port']}")
    client.connect(mqtt_conf["host"], mqtt_conf["port"])

    client.loop_forever()


if __name__ == "__main__":
    main()
