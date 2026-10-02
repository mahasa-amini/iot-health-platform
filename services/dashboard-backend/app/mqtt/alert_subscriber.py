import json
import threading
import os

import paho.mqtt.client as mqtt

from app.services.alert_stream import alert_event_stream


class AlertMQTTSubscriber:
    """
    Dashboard Backend MQTT subscriber for FINAL alerts.

    Responsibilities:
    - Subscribe to final alert topics
    - Notify UI layer that new alert data is available
    - NO persistence
    - NO business logic

    MQTT broker connection = infrastructure concern
    MQTT topics = Health Catalog concern
    """

    def __init__(self, config: dict):
        self.config = config

        # --------------------------------------------------
        # MQTT broker connection (INFRASTRUCTURE)
        # --------------------------------------------------
        self.host = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
        self.port = int(os.getenv("MQTT_BROKER_PORT", "1883"))

        # --------------------------------------------------
        # MQTT topics (FROM HEALTH CATALOG)
        # --------------------------------------------------
        mqtt_topics = config["mqtt_topics"]

        # Use strict topic (no wildcard) for dashboard
        self.alerts_topic = mqtt_topics["alerts"]["topic"]

        # --------------------------------------------------
        # MQTT client
        # --------------------------------------------------
        self._client = mqtt.Client(client_id="dashboard-backend")

    # ----------------------------------
    # MQTT callbacks
    # ----------------------------------
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[DASHBOARD-MQTT] connected to broker ✅")

            client.subscribe(self.alerts_topic, qos=1)
            print(
                f"[DASHBOARD-MQTT] subscribed to topic: {self.alerts_topic}"
            )
        else:
            print(f"[DASHBOARD-MQTT] connection failed rc={rc} ❌")

    def _on_message(self, client, userdata, msg):
        print(f"[DASHBOARD-MQTT] alert received on {msg.topic}")

        # Dashboard Backend does NOT own alert data
        # It only notifies UI that new alert data is available
        try:
            json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print("[DASHBOARD-MQTT] invalid JSON payload, ignored ❌")
            return

        alert_event_stream.publish(
            {
                "type": "alert_created"
            }
        )

    # ----------------------------------
    # Runner
    # ----------------------------------
    def start(self):
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        print(
            f"[DASHBOARD-MQTT] connecting to "
            f"{self.host}:{self.port}"
        )
        self._client.connect(self.host, self.port)

        self._client.loop_forever()

    def start_in_background(self):
        thread = threading.Thread(
            target=self.start,
            name="dashboard-mqtt-subscriber",
            daemon=True
        )
        thread.start()

        print("[DASHBOARD-MQTT] background subscriber started ")
