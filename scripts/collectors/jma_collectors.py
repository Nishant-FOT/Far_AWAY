"""
Collects real-time earthquake and tsunami data from JMA public endpoints.
Stores each event as a raw dataset sample for annotation.

JMA endpoints used:
  Earthquake list:  https://www.jma.go.jp/bosai/quake/data/list.json
  Typhoon info:     https://www.jma.go.jp/bosai/typhoon/data/
  Volcano info:     https://www.jma.go.jp/bosai/volcano/data/
"""
import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

JMA_QUAKE_URL = "https://www.jma.go.jp/bosai/quake/data/list.json"
OUTPUT_FILE = Path("data/raw/jma_earthquake_samples.jsonl")
SEEN_IDS_FILE = Path("data/raw/.jma_seen_ids.json")

HEADERS = {"User-Agent": "DisasterDetectionAgent/1.0 (research project)"}


def load_seen_ids() -> set:
    if SEEN_IDS_FILE.exists():
        return set(json.loads(SEEN_IDS_FILE.read_text()))
    return set()


def save_seen_ids(seen: set):
    SEEN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_IDS_FILE.write_text(json.dumps(list(seen)))


def shindo_to_severity(max_shindo: str) -> str:
    """
    Converts JMA Shindo (震度) scale to our severity labels.
    Shindo 1-2 → low, 3 → moderate, 4-5 → high, 5+ to 7 → critical
    """
    shindo_map = {
        "1": "low", "2": "low",
        "3": "moderate",
        "4": "high", "5-": "high", "5+": "high",
        "6-": "critical", "6+": "critical", "7": "critical",
    }
    return shindo_map.get(str(max_shindo), "unknown")


def event_to_text(event: dict, language: str = "en") -> str:
    """
    Converts a JMA earthquake event dict to a natural-language alert string.
    Generates both English and Japanese versions for bilingual training.
    """
    mag = event.get("mag", "?")
    depth = event.get("depth", "?")
    area = event.get("anm", event.get("en_anm", "Unknown area"))
    shindo = event.get("maxint", "?")
    tsunami = event.get("tsunami", 0)
    ts = event.get("at", datetime.now(timezone.utc).isoformat())

    if language == "ja":
        tsunami_str = "津波注意報が発令されました。" if tsunami else ""
        return (
            f"【気象庁】地震情報: {area}でマグニチュード{mag}、深さ{depth}kmの地震が発生しました。"
            f"最大震度: {shindo}。{tsunami_str}"
        )
    else:
        tsunami_str = " Tsunami advisory issued." if tsunami else ""
        return (
            f"[JMA] Earthquake: M{mag} at depth {depth}km near {area}. "
            f"Max seismic intensity: Shindo {shindo}.{tsunami_str}"
        )


def collect(poll_interval_seconds: int = 60, max_samples: int = 1000):
    seen = load_seen_ids()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    collected = 0

    print(f"Starting JMA earthquake collector. Target: {max_samples} samples.")

    while collected < max_samples:
        try:
            resp = requests.get(JMA_QUAKE_URL, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            events = resp.json()

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for event in events:
                    event_id = event.get("json", event.get("at", ""))
                    if event_id in seen:
                        continue

                    shindo = event.get("maxint", "1")
                    severity = shindo_to_severity(shindo)
                    tsunami_flag = bool(event.get("tsunami", 0))
                    incident_type = "tsunami" if tsunami_flag else "earthquake"

                    for lang in ["en", "ja"]:
                        raw_text = event_to_text(event, lang)
                        sample = {
                            "sample_id": f"jma-{event_id[:16]}-{lang}",
                            "source_type": "iot",
                            "raw_text": raw_text,
                            "label": {
                                "incident_type": incident_type,
                                "incident_category": "natural",
                                "severity": severity,
                                "classifier_confidence": 0.97,
                            },
                            "annotator": "jma_rule",
                            "is_synthetic": False,
                            "language": lang,
                            "location_hint": event.get("anm", ""),
                            "ambiguity_score": 0.05 if not tsunami_flag else 0.0,
                            "notes": f"JMA Shindo={shindo}, M={event.get('mag')}",
                        }
                        f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                        collected += 1

                    seen.add(event_id)
                    save_seen_ids(seen)

            print(f"Collected: {collected}/{max_samples}")

        except requests.RequestException as e:
            print(f"JMA fetch error: {e}")

        if collected < max_samples:
            time.sleep(poll_interval_seconds)

    print(f"JMA collection complete. Total samples: {collected}")


if __name__ == "__main__":
    collect()