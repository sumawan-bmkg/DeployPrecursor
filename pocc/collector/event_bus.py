"""EventBus - In-memory pub/sub event bus. Ready for MQ swap."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any
from datetime import datetime, timezone

log = logging.getLogger("event_bus")


@dataclass
class Event:
    """Generic event payload."""
    type: str = ""
    timestamp: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {"type": self.type, "timestamp": self.timestamp, "data": dict(self.data)}


class EventBus:
    """In-memory event bus. Subscribe with callback."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        subs = self._subscribers.get(event_type, [])
        if callback in subs:
            subs.remove(callback)

    def emit(self, event_type: str, data=None):
        event = Event(type=event_type, data=data or {})
        for cb in self._subscribers.get(event_type, []):
            try:
                cb(event)
            except Exception as e:
                log.error("EventBus callback error for %s: %s", event_type, e)

    def emit_event(self, event: Event):
        for cb in self._subscribers.get(event.type, []):
            try:
                cb(event)
            except Exception as e:
                log.error("EventBus callback error for %s: %s", event.type, e)


# Standard event types
class EventType:
    QC_COMPLETED = "qc.completed"
    QC_EVALUATED = "qc.evaluated"  # pure evaluation, no side effects
    ARTIFACT_ACCEPTED = "artifact.accepted"
    ARTIFACT_QUARANTINED = "artifact.quarantined"
    ARTIFACT_RETRY = "artifact.retry"
    ARTIFACT_REVIEW = "artifact.review"
    ARTIFACT_DOWNGRADE = "artifact.downgrade"
    METRICS_UPDATED = "metrics.updated"
