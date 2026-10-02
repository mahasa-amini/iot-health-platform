import asyncio
from typing import Dict, List


class PatientVitalStream:
    def __init__(self):
        self._subscribers: Dict[int, List[asyncio.Queue]] = {}
        self._last_event: Dict[int, dict] = {}  # 🔑 cache آخرین دیتا

    # -------------------------------
    async def subscribe(self, patient_id: int):
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(patient_id, []).append(queue)

        
        if patient_id in self._last_event:
            await queue.put(self._last_event[patient_id])

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._subscribers[patient_id].remove(queue)
            if not self._subscribers[patient_id]:
                del self._subscribers[patient_id]

    # -------------------------------
    async def publish(self, patient_id: int, event: dict):
       
        self._last_event[patient_id] = event

        queues = self._subscribers.get(patient_id, [])
        for q in queues:
            await q.put(event)


patient_vital_stream = PatientVitalStream()
