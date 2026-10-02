import json
import time
import random
import os
import requests
from datetime import datetime, timezone
import paho.mqtt.publish as publish

# -----------------------------
# ENV CONFIG (Docker-friendly)
# -----------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
DATA_STORAGE_URL = os.getenv("DATA_STORAGE_URL", "http://data-storage:8003")

PUBLISH_INTERVAL_SEC = 5

# Distribution
NORMAL_PROB = 0.95
WARNING_PROB = 0.03
CRITICAL_PROB = 0.02

# -----------------------------
# STANDARD Thresholds only
# (Wristband is hardware-agnostic)
# -----------------------------
THRESHOLDS = {
    "hr": {
        "NORMAL": (60, 100),
        "WARNING": (100, 120),
        "CRITICAL": (120, 160)
    },
    "spo2": {
        "NORMAL": (95, 100),
        "WARNING": (90, 95),
        "CRITICAL": (85, 90)
    },
    "temperature": {
        "NORMAL": (36.0, 37.5),
        "WARNING": (37.5, 38.5),
        "CRITICAL": (38.5, 39.5)
    },
    "battery": {
        "NORMAL": (50, 100),
        "WARNING": (20, 50),
        "CRITICAL": (0, 20)
    }
}

# -----------------------------
# Helpers
# -----------------------------
def choose_level():
    r = random.random()
    if r < NORMAL_PROB:
        return "NORMAL"
    elif r < NORMAL_PROB + WARNING_PROB:
        return "WARNING"
    else:
        return "CRITICAL"


def generate_value(vital):
    level = choose_level()
    low, high = THRESHOLDS[vital][level]

    if vital == "temperature":
        return round(random.uniform(low, high), 1)

    return random.randint(int(low), int(high))


def fetch_active_assignments():
    try:
        resp = requests.get(f"{DATA_STORAGE_URL}/api/v1/assignments/active", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[SIM][WARN] Failed to fetch assignments: {e}")
        return []


# -----------------------------
# Main loop
# -----------------------------
print("[SIM] Wristband Simulator started (STANDARD profile only)")

while True:
    print("[SIM] Fetching active assignments...")
    assignments = fetch_active_assignments()
    print(f"[SIM] Found {len(assignments)} active assignments")
    if not assignments:
        print("[SIM] No active assignments found")
        time.sleep(PUBLISH_INTERVAL_SEC)
        continue
    print("[SIM] Publishing vitals...")
    now_iso = datetime.now(timezone.utc).isoformat()

    for a in assignments:
        wristband_id = a["wristband_id"]

        vitals_payload = {
            "wristband_id": wristband_id,
            "measured_at": now_iso,
            "heart_rate": generate_value("hr"),
            "spo2": generate_value("spo2"),
            "temperature": generate_value("temperature"),
            "motion": round(random.uniform(0.0, 1.5), 2),
            "battery_level": generate_value("battery"),
        }

        topic = f"wristbands/{wristband_id}/vitals"

        publish.single(
            topic=topic,
            payload=json.dumps(vitals_payload),
            hostname=MQTT_HOST,
            port=MQTT_PORT,
            qos=0
        )

        print(f"[SIM] Published → {topic}")

    time.sleep(PUBLISH_INTERVAL_SEC)
