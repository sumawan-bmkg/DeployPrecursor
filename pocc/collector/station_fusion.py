#!/usr/bin/env python3
"""
station_fusion.py — Multi-Station Spatial-Temporal Fusion.

Groups per-station predictions into regional events.
Uses: station proximity, temporal window, prediction agreement.
"""
import json, os, time, logging, hashlib
from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path

log = logging.getLogger("station_fusion")

# Approximate station coordinates (lat, lon) for distance calculation
STATION_COORDS = {
    "ALR": (-7.30, 112.76), "AMB": (-6.85, 113.97), "CLP": (-7.15, 112.76),
    "GTO": (-0.60, 127.48), "KPY": (-0.85, 127.28), "LPS": (-8.25, 115.52),
    "LUT": (-6.65, 106.85), "LWA": (-5.38, 105.84), "LWK": (-5.45, 105.84),
    "MLB": (-8.50, 116.10), "PLU": (-7.90, 112.61), "ROT": (-1.48, 124.85),
    "SBG": (-2.53, 140.72), "SCN": (-6.25, 106.80), "SKB": (-3.65, 128.17),
    "SMI": (-1.28, 116.83), "SRG": (-6.98, 110.42), "SRO": (-7.55, 110.45),
    "TNT": (-1.50, 124.87), "TRD": (-5.05, 119.42), "TRT": (-6.17, 106.56),
    "YOG": (-7.79, 110.37),
}

# Distance thresholds
FUSION_RADIUS_KM = 500.0
FUSION_WINDOW_HOURS = 2.0


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def station_distance(s1: str, s2: str) -> float:
    """Distance in km between two stations."""
    c1 = STATION_COORDS.get(s1)
    c2 = STATION_COORDS.get(s2)
    if not c1 or not c2:
        return 999999.0
    return haversine_km(c1[0], c1[1], c2[0], c2[1])


@dataclass
class StationPrediction:
    station: str
    probability: float
    confidence: float
    uncertainty: float
    qc_score: float
    azimuth: float = 0.0
    timestamp: str = ""
    prediction_uuid: str = ""


@dataclass
class FusedEvent:
    event_id: str
    stations: List[str]
    fused_probability: float
    fused_confidence: float
    n_stations: int
    max_probability: float
    mean_probability: float
    station_predictions: list
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.event_id:
            raw = f"{self.stations}{self.created_at}"
            self.event_id = "EVT-" + hashlib.md5(raw.encode()).hexdigest()[:10]


class StationFusion:
    """
    Groups per-station predictions into regional events.

    Algorithm:
    1. For each station prediction, find nearby stations within radius
    2. Check temporal proximity (within window)
    3. If N stations agree (P > threshold), create FusedEvent
    4. Weight: station_quality * distance_inverse * probability
    """

    def __init__(self, radius_km=FUSION_RADIUS_KM, window_hours=FUSION_WINDOW_HOURS,
                 min_stations=2, prob_threshold=0.40, data_dir=None):
        self.radius_km = radius_km
        self.window_hours = window_hours
        self.min_stations = min_stations
        self.prob_threshold = prob_threshold
        self.data_dir = data_dir or "/opt/pimes/laws/runtime/validation/pdac/events"
        os.makedirs(self.data_dir, exist_ok=True)

    def fuse(self, predictions: List[StationPrediction]) -> List[FusedEvent]:
        """Group predictions into regional events."""
        if not predictions:
            return []

        # Only anomalous stations
        anomalous = [p for p in predictions if p.probability >= self.prob_threshold]
        if len(anomalous) < self.min_stations:
            log.info("Only %d anomalous stations, need %d for fusion", len(anomalous), self.min_stations)
            return []

        # Find clusters
        clusters = self._find_clusters(anomalous)
        events = []

        for cluster in clusters:
            event = self._build_event(cluster)
            events.append(event)
            self._persist_event(event)

        return events

    def _find_clusters(self, predictions: List[StationPrediction]) -> List[List[StationPrediction]]:
        """Group predictions by spatial proximity + temporal window."""
        visited = set()
        clusters = []

        for i, p1 in enumerate(predictions):
            if i in visited:
                continue
            cluster = [p1]
            visited.add(i)

            for j, p2 in enumerate(predictions):
                if j in visited:
                    continue
                # Spatial check
                dist = station_distance(p1.station, p2.station)
                if dist > self.radius_km:
                    continue
                # Temporal check
                if p1.timestamp and p2.timestamp:
                    from datetime import datetime
                    try:
                        t1 = datetime.fromisoformat(p1.timestamp.replace("Z", "+00:00"))
                        t2 = datetime.fromisoformat(p2.timestamp.replace("Z", "+00:00"))
                        hours = abs((t2 - t1).total_seconds()) / 3600
                        if hours > self.window_hours:
                            continue
                    except:
                        pass
                cluster.append(p2)
                visited.add(j)

            if len(cluster) >= self.min_stations:
                clusters.append(cluster)

        return clusters

    def _build_event(self, cluster: List[StationPrediction]) -> FusedEvent:
        """Build FusedEvent from a cluster of predictions."""
        stations = [p.station for p in cluster]
        probabilities = [p.probability for p in cluster]
        confidences = [p.confidence for p in cluster]

        # Weighted average by confidence
        total_w = sum(confidences) or 1.0
        fused_prob = sum(p.probability * p.confidence for p in cluster) / total_w
        fused_conf = sum(confidences) / len(confidences)

        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

        event = FusedEvent(
            event_id="",
            stations=stations,
            fused_probability=round(fused_prob, 4),
            fused_confidence=round(fused_conf, 4),
            n_stations=len(stations),
            max_probability=round(max(probabilities), 4),
            mean_probability=round(sum(probabilities) / len(probabilities), 4),
            station_predictions=[asdict(p) for p in cluster],
            created_at=ts,
            updated_at=ts,
        )
        return event

    def _persist_event(self, event: FusedEvent):
        fp = os.path.join(self.data_dir, f"{event.event_id}.json")
        with open(fp, "w") as f:
            json.dump(asdict(event), f, indent=2)
        log.info("FusedEvent %s: %d stations, P=%.4f", event.event_id, event.n_stations, event.fused_probability)

    def list_events(self, limit: int = 50) -> list:
        import glob
        files = sorted(glob.glob(os.path.join(self.data_dir, "EVT-*.json")))[-limit:]
        results = []
        for fp in files:
            with open(fp) as f:
                results.append(json.load(f))
        return results
