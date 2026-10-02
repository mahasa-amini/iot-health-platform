from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt # type: ignore
from sqlalchemy import text # type: ignore

from storage.local import engine, LocalStorage


class MQTTClient:
    """
    Data-Storage MQTT consumer:
    - Subscribes to vitals + final alerts topics
    - Validates JSON
    - Resolves assignment_id (for vitals)
    - Persists data into SQLite
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.storage = LocalStorage()

        # ----------------------------
        # MQTT connection
        # ----------------------------
        mqtt_cfg = self.config.get("mqtt", {})
        self.broker = mqtt_cfg.get("host") or os.getenv("MQTT_HOST", "mqtt-broker")
        self.port = int(mqtt_cfg.get("port") or os.getenv("MQTT_PORT", "1883"))
        self.keepalive = int(mqtt_cfg.get("keepalive") or os.getenv("MQTT_KEEPALIVE", "60"))

        # ----------------------------
        # Topics (from Health Catalog)
        # ----------------------------
        topics_cfg = self.config.get("topics", {})
        self.vitals_topic = (
            topics_cfg.get("vitals", {}).get("subscribe_pattern")
            or "wristbands/+/vitals"
        )
        self.alerts_topic = (
            topics_cfg.get("alerts", {}).get("subscribe_pattern")
            or "health/alerts"
        )

        # ----------------------------
        # Feature flags
        # ----------------------------
        flags = self.config.get("feature_flags", {})
        self.strict_json_validation = bool(flags.get("enable_strict_schema_validation", True))

        self._client = mqtt.Client(client_id="data-storage-service")

    # ----------------------------
    # Public API
    # ----------------------------
    def start(self) -> None:
        print("[MQTT] starting data-storage mqtt client")
        print(f"[MQTT] broker={self.broker}:{self.port}")
        print(f"[MQTT] subscribe vitals={self.vitals_topic}")
        print(f"[MQTT] subscribe alerts={self.alerts_topic}")

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        self._client.connect(self.broker, self.port, keepalive=self.keepalive)
        self._client.loop_forever()

    # ----------------------------
    # MQTT callbacks
    # ----------------------------
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] connected ✅")
            client.subscribe(self.vitals_topic, qos=0)
            client.subscribe(self.alerts_topic, qos=1)
            print("[MQTT] subscribed ✅")
        else:
            print(f"[MQTT] connect failed rc={rc} ❌")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] disconnected rc={rc}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        raw = msg.payload

        print(f"[MQTT] message received topic={topic}")

        payload = self._decode_json(raw)
        if payload is None:
            return

        if topic.startswith("health/alerts"):
            self._handle_alert(payload)
            return

        if topic.startswith("wristbands/") and topic.endswith("/vitals"):
            self._handle_vitals(payload)
            return

        print("[MQTT] unhandled topic, ignored")

    # ----------------------------
    # Helpers
    # ----------------------------
    def _decode_json(self, raw: bytes) -> Optional[Dict[str, Any]]:
        try:
            obj = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            print(f"[MQTT] Invalid JSON payload: {raw!r}")
            return None

        if self.strict_json_validation and not isinstance(obj, dict):
            print(f"[MQTT] JSON must be an object, got {type(obj)}")
            return None

        return obj

    def _resolve_assignment_id(self, wristband_id: int) -> Optional[int]:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT assignment_id
                    FROM WRISTBAND_ASSIGNMENT
                    WHERE wristband_id = :wid
                      AND end_date IS NULL
                    """
                ),
                {"wid": wristband_id},
            ).fetchone()

        return int(row[0]) if row else None

    # ----------------------------
    # Handlers
    # ----------------------------
    def _handle_vitals(self, payload: Dict[str, Any]) -> None:
        wristband_id = payload.get("wristband_id")
        if wristband_id is None:
            print("[VITAL] wristband_id missing, drop message")
            return

        assignment_id = self._resolve_assignment_id(int(wristband_id))
        if assignment_id is None:
            print(f"[VITAL] No active assignment for wristband {wristband_id}")
            return

        self.storage.save_vital(assignment_id=assignment_id, data=payload)
        print(f"[VITAL] stored ✅ assignment_id={assignment_id}")

    def _handle_alert(self, payload: Dict[str, Any]) -> None:
        print("[ALERT] received:", payload)

        assignment_id = payload.get("assignment_id")
        if assignment_id is None:
            print("[ALERT] assignment_id missing, drop alert")
            return

        # Minimal validation (schema enforced elsewhere)
        alert_data = {
            "alert_type": payload.get("alert_type"),
            "severity": payload.get("severity"),
            "status": payload.get("status"),
            "threshold_profile": payload.get("threshold_profile"),
            "metric": payload.get("metric"),
            "value": payload.get("value"),
            "description": payload.get("description"),
            "full_description": payload.get("full_description"),
            "generated_at": payload.get("generated_at"),
        }

        self.storage.save_alert(assignment_id=int(assignment_id), data=alert_data)
        print(f"[ALERT] stored ✅ assignment_id={assignment_id}")


# Backward-compatible entry point
def start_mqtt(config: Optional[Dict[str, Any]] = None) -> None:
    MQTTClient(config=config).start()
