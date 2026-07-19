"""P7 Ground Truth Collector — fetch earthquake catalog from USGS."""
import urllib.request
import json
from datetime import datetime, timezone
from typing import List


class EQEvent:
    __slots__ = ('mag', 'place', 'lat', 'lon', 'depth_km', 'time_utc', 'eqid', 'latlon_hash')
    def __init__(self, mag, place, lat, lon, depth_km, time_utc, eqid):
        self.mag = mag
        self.place = place
        self.lat = lat
        self.lon = lon
        self.depth_km = depth_km
        self.time_utc = time_utc
        self.eqid = eqid
        self.latlon_hash = f"{lat:.2f}{lon:.2f}"

    def to_dict(self):
        return dict(mag=self.mag, place=self.place, lat=self.lat, lon=self.lon,
                    depth_km=self.depth_km, time_utc=self.time_utc, eqid=self.eqid)

    def __repr__(self):
        return f"EQEvent(M{self.mag:.1f} {self.place})"


class GroundTruthCollector:
    """Fetch earthquake events from USGS FDSN API."""

    def __init__(self, min_magnitude=4.0, radius_deg=10.0, station_lat=0.0, station_lon=110.0):
        self.min_magnitude = min_magnitude
        self.radius_deg = radius_deg
        self.station_lat = station_lat
        self.station_lon = station_lon

    def fetch_events(self, start_date: str, end_date: str) -> List[EQEvent]:
        """Fetch events from USGS. Dates as 'YYYY-MM-DD'."""
        url = (
            f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
            f"format=geojson&starttime={start_date}&endtime={end_date}"
            f"&minmagnitude={self.min_magnitude}&orderby=time"
        )
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read())
        except Exception:
            return []

        events = []
        for e in data.get('features', []):
            p = e['properties']
            coords = e['geometry']['coordinates']
            t = datetime.fromtimestamp(p['time'] / 1000, tz=timezone.utc)
            events.append(EQEvent(
                mag=p['mag'], place=p['place'],
                lat=coords[1], lon=coords[0], depth_km=coords[2],
                time_utc=t.strftime("%Y-%m-%dT%H:%M:%S"), eqid=e['id']
            ))
        return events

    def match_predictions(self, events, predictions):
        matched = []
        for ev in events:
            best = None; best_dist = float('inf')
            for pred in predictions:
                lat = getattr(pred, '_eq_lat', self.station_lat)
                lon = getattr(pred, '_eq_lon', self.station_lon)
                dist = self._haversine(ev.lat, ev.lon, lat, lon)
                if dist < self.radius_deg and dist < best_dist:
                    best = pred; best_dist = dist
            if best:
                matched.append((ev, best, best_dist))
        return matched

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        import math
        R = 6371.0
        dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
