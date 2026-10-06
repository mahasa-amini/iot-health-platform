import json
import os
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

# ----------------------------------
# Health Catalog
# ----------------------------------
HEALTH_CATALOG_URL = os.getenv(
    "HEALTH_CATALOG_URL",
    "http://health-catalog:8000",
)

THRESHOLDS_ENDPOINT = "/config/thresholds"
MQTT_TOPICS_ENDPOINT = "/config/mqtt/topics"
ENVIRONMENTS_ENDPOINT = "/config/environments"

# ----------------------------------
# Data Storage API
# ----------------------------------
DATA_STORAGE_URL = os.getenv(
    "DATA_STORAGE_URL",
    "http://data-storage:8003",
)
DATA_STORAGE_BASE = DATA_STORAGE_URL
ASSIGNMENT_ENDPOINT = "/api/v1/assignments/by-wristband/{}"

# ----------------------------------
# Global configs (loaded at startup)
# ----------------------------------
THRESHOLDS = {}
MQTT_TOPICS = {}
ENV_CONFIG = {}

DEFAULT_PROFILE = "STANDARD"
PROFILE_CACHE = {}  # wristband_id -> threshold_profile


# ----------------------------------
# Helpers
# ----------------------------------
def load_from_catalog(endpoint: str) -> dict:
    res = requests.get(f"{HEALTH_CATALOG_URL}{endpoint}")
    res.raise_for_status()
    return res.json()["data"]


def resolve_severity(value, ranges):
    for level in ["CRITICAL", "WARNING", "NORMAL"]:
        low, high = ranges.get(level)
        if (low is None or value >= low) and (high is None or value < high):
            return level
    return "NORMAL"

def get_profile_for_wristband(wristband_id: int) -> str:
    """
    Resolve patient threshold profile via Data Storage.
    Cached per wristband.
    """
    if wristband_id in PROFILE_CACHE:
        return PROFILE_CACHE[wristband_id]

    try:
        resp = requests.get(
            DATA_STORAGE_BASE + ASSIGNMENT_ENDPOINT.format(wristband_id),
            timeout=1.5
        )
        if resp.status_code != 200:
            raise RuntimeError("assignment not found")

        profile = resp.json().get("threshold_profile", DEFAULT_PROFILE)
        PROFILE_CACHE[wristband_id] = profile
        return profile

    except Exception as e:
        print(f"[RISK] profile lookup failed for wristband {wristband_id}: {e}")
        return DEFAULT_PROFILE


# ----------------------------------
# MQTT callbacks
# ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[RISK] Connected to MQTT broker (rc={reason_code})")

    vitals_topic = MQTT_TOPICS["mqtt_topics"]["vitals"]["subscribe_pattern"]
    client.subscribe(vitals_topic, qos=0)

    print(f"[RISK] Subscribed to {vitals_topic}")


def on_message(client, userdata, msg):
    print(f"[RISK] Message received on {msg.topic}")

    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("[RISK] Invalid JSON payload")
        return

    wristband_id = payload.get("wristband_id")
    if wristband_id is None:
        print("[RISK] wristband_id missing")
        return

    # 1️⃣ Resolve patient profile
    profile = get_profile_for_wristband(int(wristband_id))
    profile_thresholds = THRESHOLDS["profiles"].get(profile)

    if not profile_thresholds:
        print(f"[RISK] Unknown profile {profile}")
        return

    highest_severity = "NORMAL"
    breached_metric = None
    breached_value = None

    # 2️⃣ Evaluate all vitals
    metric_aliases = {
        "heart_rate": "hr",
        "battery_level": "battery",
    }

    for metric, value in payload.items():
        threshold_metric = metric_aliases.get(metric, metric)

        if threshold_metric not in profile_thresholds or value is None:
            continue

        severity = resolve_severity(
            value,
            profile_thresholds[threshold_metric],
        )

        if severity == "CRITICAL":
            highest_severity = "CRITICAL"
            breached_metric = metric
            breached_value = value
            break

        if severity == "WARNING" and highest_severity != "CRITICAL":
            highest_severity = "WARNING"
            breached_metric = metric
            breached_value = value

    if highest_severity == "NORMAL":
        print("[RISK] All vitals normal")
        return

    # 3️⃣ Build risk event (intermediate)
    risk_event = {
        "wristband_id": wristband_id,
        "alert_type": "THRESHOLD_BREACH",
        "severity": highest_severity,
        "threshold_profile": profile,
        "vital": breached_metric,
        "value": breached_value,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    topic = MQTT_TOPICS["mqtt_topics"]["risk_events"]["template"].format(
        wristband_id=wristband_id
    )

    client.publish(topic, json.dumps(risk_event), qos=1)
    print(f"[RISK] Risk event published → {risk_event}")


# ----------------------------------
# Main
# ----------------------------------
def main():
    global THRESHOLDS, MQTT_TOPICS, ENV_CONFIG

    print("[RISK] Starting Risk Analysis Service")

    # Load configs
    THRESHOLDS = load_from_catalog(THRESHOLDS_ENDPOINT)
    MQTT_TOPICS = load_from_catalog(MQTT_TOPICS_ENDPOINT)
    ENV_CONFIG = load_from_catalog(ENVIRONMENTS_ENDPOINT)

    active_env = ENV_CONFIG["active_environment"]
    mqtt_conf = ENV_CONFIG["environments"][active_env]["mqtt"]

    # MQTT client
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="risk-analysis-service")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[RISK] Connecting to MQTT {mqtt_conf['host']}:{mqtt_conf['port']}")
    client.connect(mqtt_conf["host"], mqtt_conf["port"])

    client.loop_forever()


if __name__ == "__main__":
    main()
