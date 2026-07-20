#!/usr/bin/env python3
"""
event_manager.py — Event lifecycle management.

Tracks seismic precursor events from detection through decay.
States: NEW → ACTIVE → PEAK → DECAY → CLOSED
"""
import json, os, time, logging
from enum import Enum
from typing import List, Optional
from pathlib import Path

log = logging.getLogger("event_manager")

EVENT_DIR = "/opt/pimes/laws/runtime/validation/pdac/events"
os.makedirs(EVENT_DIR, exist_ok=True)


class EventState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    PEAK = "PEAK"
    DECAY = "DECAY"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class Event:
    """Single event with lifecycle."""
    def __init__(self, event_id: str, stations: list, fused_probability: float):
        self.event_id = event_id
        self.state = EventState.NEW
        self.stations = stations
        self.fused_probability = fused_probability
        self.peak_probability = fused_probability
        self.history = []  # [{state, probability, timestamp, n_stations}]
        self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.updated_at = self.created_at
        self.closed_at = None

    def transition(self, new_state: str, probability: float, n_stations: int):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.history.append({
            "from_state": self.state.value,
            "to_state": new_state,
            "probability": round(probability, 4),
            "n_stations": n_stations,
            "timestamp": ts,
        })
        self.state = EventState(new_state)
        self.updated_at = ts
        if probability > self.peak_probability:
            self.peak_probability = probability
        if new_state in ("CLOSED", "EXPIRED"):
            self.closed_at = ts

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "state": self.state.value,
            "stations": self.stations,
            "fused_probability": self.fused_probability,
            "peak_probability": self.peak_probability,
            "n_transitions": len(self.history),
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        e = cls(d["event_id"], d["stations"], d["fused_probability"])
        e.state = EventState(d.get("state", "NEW"))
        e.peak_probability = d.get("peak_probability", e.fused_probability)
        e.history = d.get("history", [])
        e.created_at = d.get("created_at", "")
        e.updated_at = d.get("updated_at", "")
        e.closed_at = d.get("closed_at")
        return e


class EventManager:
    """
    Manages event lifecycle.

    - Receives FusedEvents from station_fusion
    - Creates or updates events (de-duplicates)
    - Transitions states based on probability trends
    - Auto-closes events after timeout
    """

    def __init__(self, data_dir: str = EVENT_DIR, close_after_hours: float = 24.0):
        self.data_dir = data_dir
        self.close_after_hours = close_after_hours
        os.makedirs(data_dir, exist_ok=True)

    def process_fused_event(self, fused_event) -> Event:
        """Process a FusedEvent from station_fusion."""
        fe = fused_event
        if hasattr(fused_event, 'to_dict'):
            fe_dict = fused_event.to_dict() if hasattr(fused_event, 'to_dict') else {}
        elif isinstance(fused_event, dict):
            fe_dict = fused_event
        else:
            fe_dict = {}

        event_id = fe_dict.get("event_id", "")
        stations = fe_dict.get("stations", [])
        prob = fe_dict.get("fused_probability", 0.0)

        # Check for existing event covering these stations
        existing = self._find_active_by_stations(stations)
        if existing:
            existing.transition(existing.state.value, prob, len(stations))
            self._update_state(existing, prob, len(stations))
            self._persist(existing)
            return existing

        # New event
        event = Event(event_id, stations, prob)
        self._update_state(event, prob, len(stations))
        self._persist(event)
        log.info("New event %s: %d stations, P=%.4f", event.event_id, len(stations), prob)
        return event

    def _update_state(self, event: Event, prob: float, n_stations: int):
        """Transition event based on probability."""
        if prob >= 0.90 and event.state != EventState.PEAK:
            event.transition(EventState.PEAK.value, prob, n_stations)
        elif prob >= 0.70 and event.state == EventState.NEW:
            event.transition(EventState.ACTIVE.value, prob, n_stations)
        elif prob < 0.30 and event.state in (EventState.ACTIVE, EventState.PEAK):
            event.transition(EventState.DECAY.value, prob, n_stations)

    def close_stale_events(self):
        """Close events older than close_after_hours."""
        import glob
        now = time.time()
        for fp in glob.glob(os.path.join(self.data_dir, "EVT-*.json")):
            try:
                with open(fp) as f:
                    d = json.load(f)
                if d.get("state") in ("CLOSED", "EXPIRED"):
                    continue
                created = d.get("created_at", "")
                if created:
                    from datetime import datetime
                    ct = datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp()
                    if (now - ct) / 3600 > self.close_after_hours:
                        event = Event.from_dict(d)
                        event.transition(EventState.CLOSED.value, d.get("fused_probability", 0), len(d.get("stations", [])))
                        self._persist(event)
                        log.info("Auto-closed event %s after %.0fh", event.event_id, (now - ct) / 3600)
            except Exception as e:
                log.error("Error processing %s: %s", fp, str(e)[:100])

    def _find_active_by_stations(self, stations: list) -> Optional[Event]:
        """Find active event covering same stations."""
        import glob
        for fp in glob.glob(os.path.join(self.data_dir, "EVT-*.json")):
            try:
                with open(fp) as f:
                    d = json.load(f)
                if d.get("state") in ("CLOSED", "EXPIRED"):
                    continue
                existing_stations = set(d.get("stations", []))
                overlap = existing_stations & set(stations)
                if len(overlap) >= max(1, len(stations) // 2):
                    return Event.from_dict(d)
            except:
                pass
        return None

    def _persist(self, event: Event):
        fp = os.path.join(self.data_dir, f"{event.event_id}.json")
        with open(fp, "w") as f:
            json.dump(event.to_dict(), f, indent=2)

    def list_events(self, state: str = "", limit: int = 50) -> list:
        import glob
        files = sorted(glob.glob(os.path.join(self.data_dir, "EVT-*.json")))[-limit:]
        results = []
        for fp in files:
            with open(fp) as f:
                d = json.load(f)
                if state and d.get("state") != state:
                    continue
                results.append(d)
        return results

    def get_event(self, event_id: str) -> Optional[dict]:
        fp = os.path.join(self.data_dir, f"{event_id}.json")
        if os.path.exists(fp):
            with open(fp) as f:
                return json.load(f)
        return None
