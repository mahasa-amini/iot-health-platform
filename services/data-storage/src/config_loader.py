import os
import time
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


# ----------------------------
# Internal helpers
# ----------------------------
def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def _get_json(url: str) -> dict:
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


# ----------------------------
# Public API
# ----------------------------
def load_health_catalog_config(
    retries: int = 5,
    delay_seconds: int = 2
) -> dict:
    """
    Load configuration required by Data Storage Service
    from Health Catalog.
    """
    hc_base = os.getenv("HEALTH_CATALOG_URL", "http://health-catalog:8000")

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(f"[CONFIG] Loading Health Catalog (attempt {attempt}/{retries})")

            # Service registry (mainly for REST exposure / documentation)
            services = _get_json(
                _url(hc_base, "/registry/services")
            )["data"]

            # MQTT topics contract
            topics = _get_json(
                _url(hc_base, "/config/mqtt/topics")
            )["data"]

            # Alert contract (schema + lifecycle)
            alerts = _get_json(
                _url(hc_base, "/config/alerts")
            )["data"]

            # Environments (MQTT host/port resolution)
            environments = _get_json(
                _url(hc_base, "/config/environments")
            )["data"]

            active_env = environments["active_environment"]
            env_cfg = environments["environments"].get(active_env, {})

            config = {
                "environment": active_env,
                "mqtt": env_cfg.get("mqtt", {}),
                "topics": topics,
                "alerts": alerts,
                "services": services
            }

            print("[CONFIG] Health Catalog loaded successfully")
            print(f"[CONFIG] Active environment: {active_env}")

            return config

        except (HTTPError, URLError, KeyError, json.JSONDecodeError) as e:
            last_error = e
            print(
                f"[CONFIG] Health Catalog not ready "
                f"(attempt {attempt}/{retries}): {e}"
            )
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Health Catalog unavailable after {retries} attempts: {last_error}"
    )
