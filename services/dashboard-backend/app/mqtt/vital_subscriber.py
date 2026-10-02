import json
import threading
import os
import asyncio

import paho.mqtt.client as mqtt

from app.services.assignment_cache import get_patient_id_for_wristband
from app.services.patient_vital_stream import patient_vital_stream


class VitalMQTTSubscriber:
    """
    Dashboard Backend MQTT subscriber for RAW vitals.
    """

    def __init__(self, config: dict):
        self.config = config

        self.host = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
        self.port = int(os.getenv("MQTT_BROKER_PORT", "1883"))

        mqtt_topics = config["mqtt_topics"]
        self.vitals_topic = mqtt_topics["vitals"]["subscribe_pattern"]

        self._client = mqtt.Client(client_id="dashboard-backend-vitals")

        #  event loop اصلی FastAPI
        self.loop = asyncio.get_event_loop()

    # ----------------------------------
    # MQTT callbacks
    # ----------------------------------
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[VITAL-MQTT] connected to broker ✅")
            client.subscribe(self.vitals_topic, qos=0)
            print(f"[VITAL-MQTT] subscribed to {self.vitals_topic}")
        else:
            print(f"[VITAL-MQTT] connection failed rc={rc} ❌")

    def _on_message(self, client, userdata, msg):
        print(f"[VITAL-MQTT] message received on {msg.topic}")

        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print("[VITAL-MQTT] invalid JSON payload ❌")
            return

        wristband_id = payload.get("wristband_id")
        if wristband_id is None:
            print("[VITAL-MQTT] wristband_id missing")
            return
        
        print("[VITAL-MQTT] payload:", payload)

        patient_id = get_patient_id_for_wristband(int(wristband_id))


        print(
            f"[VITAL-MQTT] mapping wristband {wristband_id} → patient {patient_id}"
                )
        

        
        if patient_id is None:
            print(f"[VITAL-MQTT] no patient for wristband {wristband_id}")
            return

        event = {
            "type": "vital_update",
            "patient_id": patient_id,
            "data": payload
        }

        #  thread-safe async publish
        asyncio.run_coroutine_threadsafe(
            patient_vital_stream.publish(patient_id, event),
            self.loop
        )

    # ----------------------------------
    # Runner
    # ----------------------------------
    def start(self):
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        print(f"[VITAL-MQTT] connecting to {self.host}:{self.port}")
        self._client.connect(self.host, self.port)
        self._client.loop_forever()

    def start_in_background(self):
        thread = threading.Thread(
            target=self.start,
            name="dashboard-vital-subscriber",
            daemon=True
        )
        thread.start()

        print("[VITAL-MQTT] background subscriber started 🚀")
