"""
Collects Japan-region earthquake data from USGS FDSN API.
Generates English-language earthquake training samples.
"""
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OUTPUT_FILE = Path("data/raw/usgs_earthquake_samples.jsonl")

JAPAN_BBOX = {
    "minlatitude": 24,
    "maxlatitude": 46,
    "minlongitude": 122,
    "maxlongitude": 146,
}


def magnitude_to_severity(mag: float) -> str:
    if mag < 4.0:
        return "low"
    if mag < 5.5:
        return "moderate"
    if mag < 6.5:
        return "high"
    return "critical"


def collect(days_back: int = 365, min_magnitude: float = 3.0):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)

    params = {
        **JAPAN_BBOX,
        "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "format": "geojson",
        "limit": 2000,
        "orderby": "time",
    }

    print("Fetching USGS earthquake data for Japan region...")
    resp = requests.get(USGS_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    print(f"Events fetched: {len(features)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for feat in features:
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            mag = props.get("mag", 0)
            place = props.get("place", "Japan region")
            tsunami_flag = props.get("tsunami", 0)
            ts = datetime.fromtimestamp(
                props["time"] / 1000, tz=timezone.utc
            ).isoformat()

            incident_type = "tsunami" if tsunami_flag else "earthquake"
            severity = magnitude_to_severity(mag)

            raw_text = (
                f"USGS Alert: M{mag:.1f} earthquake {place}. "
                f"Depth: {coords[2]:.1f}km."
            )
            if tsunami_flag:
                raw_text += " Tsunami threat reported."

            sample = {
                "sample_id": f"usgs-{feat['id']}",
                "source_type": "iot",
                "raw_text": raw_text,
                "label": {
                    "incident_type": incident_type,
                    "incident_category": "natural",
                    "severity": severity,
                    "classifier_confidence": 0.95,
                },
                "annotator": "usgs_rule",
                "is_synthetic": False,
                "language": "en",
                "location_hint": place,
                "ambiguity_score": 0.0,
                "notes": f"USGS M{mag}, depth={coords[2]:.1f}km",
            }
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            written += 1

    print(f"USGS samples written: {written}")


if __name__ == "__main__":
    collect()