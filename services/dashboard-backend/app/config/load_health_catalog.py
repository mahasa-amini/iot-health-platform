import os
import time
import requests

HEALTH_CATALOG_URL = os.getenv(
    "HEALTH_CATALOG_URL",
    "http://health-catalog:8000"
)


def load_health_catalog_config(retries: int = 10, delay: int = 3) -> dict:
    """
    Load ONLY configuration owned by Health Catalog.

    Dashboard Backend gets:
    - MQTT topics (from Health Catalog)
    - Active environment

    MQTT broker connection info is INFRASTRUCTURE
    and must NOT come from Health Catalog.
    """

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(f"[DASHBOARD] loading Health Catalog (attempt {attempt})")

            topics_resp = requests.get(
                f"{HEALTH_CATALOG_URL}/config/mqtt/topics",
                timeout=5
            )
            topics_resp.raise_for_status()

            env_resp = requests.get(
                f"{HEALTH_CATALOG_URL}/config/environments",
                timeout=5
            )
            env_resp.raise_for_status()

            mqtt_topics = topics_resp.json()["data"]["mqtt_topics"]
            environment = env_resp.json()["data"]

            return {
                "mqtt_topics": mqtt_topics,
                "environment": environment,
            }

        except Exception as e:
            last_error = e
            print(
                f"[DASHBOARD] Health Catalog not ready "
                f"(attempt {attempt}/{retries}): {e}"
            )
            time.sleep(delay)

    raise RuntimeError(
        f"Health Catalog unavailable after {retries} attempts: {last_error}"
    )
