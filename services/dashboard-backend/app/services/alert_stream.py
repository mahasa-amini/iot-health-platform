from typing import Set, Dict, Any
import threading
import queue


class AlertEventStream:
    """
    In-memory fan-out stream for alert events.

    - MQTT subscriber publishes events
    - WebSocket/SSE clients subscribe
    - No persistence
    - No business logic
    """

    def __init__(self):
        self._subscribers: Set[queue.Queue] = set()
        self._lock = threading.Lock()

    # ----------------------------
    # Subscription management
    # ----------------------------
    def subscribe(self) -> queue.Queue:
        """
        Register a new subscriber and return its queue.
        """
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        """
        Remove a subscriber queue.
        """
        with self._lock:
            self._subscribers.discard(q)

    # ----------------------------
    # Publish
    # ----------------------------
    def publish(self, event: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers.
        """
        with self._lock:
            subscribers = list(self._subscribers)

        for q in subscribers:
            try:
                q.put_nowait(event)
            except Exception:
                # If queue is full or broken, ignore
                pass


# Singleton instance
alert_event_stream = AlertEventStream()
