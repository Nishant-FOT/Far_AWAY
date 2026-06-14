"""
Synthetic disaster data generator for Japan.
Uses an Ollama model (default: qwen3:8b) as teacher model.

Usage:
    python scripts/generate_synthetic_japan.py --count 500 --output data/synthetic/synthetic_japan.jsonl --model qwen3:8b --timeout 300
"""

import argparse
import json
import random
import time
import uuid
from pathlib import Path

import requests


OLLAMA_URL = "http://localhost:11434/api/chat"

INCIDENT_TYPES = [
    "earthquake", "tsunami", "typhoon", "flood", "landslide",
    "volcanic_eruption", "urban_fire", "building_collapse",
    "coastal_storm_surge", "heavy_snow_emergency",
]

SEVERITIES = ["low", "moderate", "high", "critical"]

SOURCE_STYLES = [
    "formal_japanese_news",
    "english_news",
    "japanese_social_media",
    "english_social_media",
    "iot_sensor_alert",
    "government_alert_japanese",
]

JAPANESE_PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]

PROMPTS = {
    ("earthquake", "formal_japanese_news"):
        "/no_think {location}で地震が発生した。incident_type must be earthquake, incident_category must be natural, severity must be {severity}, language must be ja. マグニチュード・震度・負傷者数を含む気象庁スタイルの日本語ニュース文を1〜2文書いてください。",

    ("earthquake", "english_news"):
        "/no_think incident_type must be earthquake, incident_category must be natural, severity must be {severity}, language must be en. Write 1-2 formal English news sentences about a Japan earthquake near {location}. Include magnitude, depth, and casualty numbers.",

    ("earthquake", "japanese_social_media"):
        "/no_think incident_type must be earthquake, incident_category must be natural, severity must be {severity}, language must be ja. {location}の地震についてX（旧Twitter）風の日本語投稿を1文書いてください。ハッシュタグを含めること。",

    ("tsunami", "government_alert_japanese"):
        "/no_think incident_type must be tsunami, incident_category must be natural, severity must be {severity}, language must be ja. {location}沿岸への津波警報の気象庁告知文を1〜2文書いてください。予想波高・避難指示を含めること。",

    ("tsunami", "english_social_media"):
        "/no_think incident_type must be tsunami, incident_category must be natural, severity must be {severity}, language must be en. Write 1 urgent English tweet about a tsunami warning near {location}, Japan. May have typos.",

    ("typhoon", "iot_sensor_alert"):
        "/no_think incident_type must be typhoon, incident_category must be natural, severity must be {severity}, language must be en. Write a weather station IoT alert for a typhoon near {location}. Include wind speed km/h, pressure hPa, rainfall mm/h.",

    ("typhoon", "formal_japanese_news"):
        "/no_think incident_type must be typhoon, incident_category must be natural, severity must be {severity}, language must be ja. {location}に接近する台風の日本語ニュース文を1〜2文書いてください。台風番号・最大風速・予想雨量を含めること。",

    ("flood", "formal_japanese_news"):
        "/no_think incident_type must be flood, incident_category must be natural, severity must be {severity}, language must be ja. {location}の洪水・河川氾濫についての日本語ニュース文を1〜2文書いてください。浸水深・避難者数を含めること。",

    ("volcanic_eruption", "government_alert_japanese"):
        "/no_think incident_type must be volcanic_eruption, incident_category must be natural, severity must be {severity}, language must be ja. {location}近辺の火山噴火に関する気象庁告知文を1〜2文書いてください。噴火警戒レベル・入山規制を含めること。",

    ("heavy_snow_emergency", "formal_japanese_news"):
        "/no_think incident_type must be heavy_snow_emergency, incident_category must be natural, severity must be {severity}, language must be ja. {location}の大雪緊急事態についての日本語ニュース文を1〜2文書いてください。積雪量・交通障害・孤立集落を含めること。",
}

GENERIC_PROMPT = (
    "/no_think incident_type must be {incident_type}, "
    "severity must be {severity}. "
    "Use language that matches style {style}. "
    "Write 1-2 sentences about a disaster in {location}, Japan."
)

ALLOWED_INCIDENT_TYPES = set(INCIDENT_TYPES)
ALLOWED_CATEGORIES = {"natural", "man_made", "infrastructure"}
ALLOWED_SEVERITIES = set(SEVERITIES)
ALLOWED_LANGUAGES = {"ja", "en", "mixed"}

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "raw_text": {"type": "string"},
        "label": {
            "type": "object",
            "properties": {
                "incident_type": {
                    "type": "string",
                    "enum": [
                        "earthquake", "tsunami", "typhoon", "flood", "landslide",
                        "volcanic_eruption", "urban_fire", "building_collapse",
                        "coastal_storm_surge", "heavy_snow_emergency"
                    ]
                },
                "incident_category": {
                    "type": "string",
                    "enum": ["natural", "man_made", "infrastructure"]
                },
                "severity": {
                    "type": "string",
                    "enum": ["low", "moderate", "high", "critical"]
                },
                "classifier_confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            },
            "required": [
                "incident_type",
                "incident_category",
                "severity",
                "classifier_confidence"
            ],
            "additionalProperties": False
        },
        "ambiguity_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "language": {
            "type": "string",
            "enum": ["ja", "en", "mixed"]
        }
    },
    "required": ["raw_text", "label", "ambiguity_score", "language"],
    "additionalProperties": False
}

INCIDENT_TYPE_MAP = {
    "地震": "earthquake",
    "津波": "tsunami",
    "台風": "typhoon",
    "洪水": "flood",
    "河川氾濫": "flood",
    "浸水": "flood",
    "土砂崩れ": "landslide",
    "地滑り": "landslide",
    "火山噴火": "volcanic_eruption",
    "噴火": "volcanic_eruption",
    "火災": "urban_fire",
    "大規模火災": "urban_fire",
    "建物崩壊": "building_collapse",
    "ビル崩壊": "building_collapse",
    "高潮": "coastal_storm_surge",
    "大雪": "heavy_snow_emergency",
    "暴風雪": "heavy_snow_emergency",
}

CATEGORY_MAP = {
    "自然災害": "natural",
    "自然": "natural",
    "人的災害": "man_made",
    "人為災害": "man_made",
    "インフラ": "infrastructure",
    "インフラ災害": "infrastructure",
}

SEVERITY_MAP = {
    "低": "low",
    "軽度": "low",
    "中": "moderate",
    "中程度": "moderate",
    "高": "high",
    "重度": "high",
    "重大": "critical",
    "危機的": "critical",
}

LANGUAGE_MAP = {
    "jp": "ja",
    "japanese": "ja",
    "english": "en",
}

DEFAULT_CATEGORY_BY_INCIDENT = {
    "earthquake": "natural",
    "tsunami": "natural",
    "typhoon": "natural",
    "flood": "natural",
    "landslide": "natural",
    "volcanic_eruption": "natural",
    "urban_fire": "man_made",
    "building_collapse": "infrastructure",
    "coastal_storm_surge": "natural",
    "heavy_snow_emergency": "natural",
}


def check_ollama() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=5)
        return r.ok
    except requests.RequestException:
        return False


def call_ollama(prompt: str, model: str, timeout: int) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": JSON_SCHEMA,
        "options": {
            "temperature": 0,
            "num_predict": 512
        },
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def parse_response(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def normalize_text_value(value):
    if not isinstance(value, str):
        return value
    return value.strip().lower()


def normalize_parsed(parsed: dict, expected_incident: str, expected_severity: str, expected_style: str):
    if not isinstance(parsed, dict):
        return None

    label = parsed.get("label", {})
    if not isinstance(label, dict):
        return None

    incident_type = label.get("incident_type")
    category = label.get("incident_category")
    severity = label.get("severity")
    language = parsed.get("language")

    if isinstance(incident_type, str):
        incident_type = incident_type.strip()
        incident_type = INCIDENT_TYPE_MAP.get(incident_type, incident_type)
        incident_type = normalize_text_value(incident_type)

    if isinstance(category, str):
        category = category.strip()
        category = CATEGORY_MAP.get(category, category)
        category = normalize_text_value(category)

    if isinstance(severity, str):
        severity = severity.strip()
        severity = SEVERITY_MAP.get(severity, severity)
        severity = normalize_text_value(severity)

    if isinstance(language, str):
        language = language.strip().lower()
        language = LANGUAGE_MAP.get(language, language)

    label["incident_type"] = incident_type
    label["incident_category"] = category
    label["severity"] = severity
    parsed["language"] = language

    if not label.get("incident_category") and incident_type in DEFAULT_CATEGORY_BY_INCIDENT:
        label["incident_category"] = DEFAULT_CATEGORY_BY_INCIDENT[incident_type]

    if expected_style.startswith("japanese") or expected_style.endswith("japanese") or "japanese" in expected_style:
        if parsed.get("language") not in {"ja", "mixed"}:
            parsed["language"] = "ja"

    if expected_style.startswith("english") or "english" in expected_style:
        if parsed.get("language") not in {"en", "mixed"}:
            parsed["language"] = "en"

    if label.get("incident_type") != expected_incident:
        label["incident_type"] = expected_incident

    if label.get("severity") != expected_severity:
        label["severity"] = expected_severity

    if "classifier_confidence" in label:
        try:
            label["classifier_confidence"] = float(label["classifier_confidence"])
        except (TypeError, ValueError):
            label["classifier_confidence"] = 0.85

    if "ambiguity_score" in parsed:
        try:
            parsed["ambiguity_score"] = float(parsed["ambiguity_score"])
        except (TypeError, ValueError):
            parsed["ambiguity_score"] = 0.2

    parsed["label"] = label
    return parsed


def is_valid_parsed(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    if not isinstance(parsed.get("raw_text"), str) or not parsed["raw_text"].strip():
        return False
    if not isinstance(parsed.get("label"), dict):
        return False

    label = parsed["label"]

    if label.get("incident_type") not in ALLOWED_INCIDENT_TYPES:
        return False
    if label.get("incident_category") not in ALLOWED_CATEGORIES:
        return False
    if label.get("severity") not in ALLOWED_SEVERITIES:
        return False
    if parsed.get("language") not in ALLOWED_LANGUAGES:
        return False

    try:
        cc = float(label.get("classifier_confidence"))
        if not (0.0 <= cc <= 1.0):
            return False
    except (TypeError, ValueError):
        return False

    try:
        amb = float(parsed.get("ambiguity_score"))
        if not (0.0 <= amb <= 1.0):
            return False
    except (TypeError, ValueError):
        return False

    return True


def get_prompt(incident_type: str, style: str, location: str, severity: str) -> str:
    template = PROMPTS.get((incident_type, style), GENERIC_PROMPT)
    return template.format(
        incident_type=incident_type,
        location=location,
        severity=severity,
        style=style,
    )


def main(count: int, output_path: str, model: str, timeout: int, debug: bool):
    if not check_ollama():
        print("ERROR: Ollama not reachable at http://localhost:11434")
        print("Run 'ollama serve' in a separate terminal first.")
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    generated = 0
    failed = 0
    max_retries = 3

    print(f"Model   : {model}")
    print(f"Timeout : {timeout}s")
    print(f"Output  : {output_path}")
    print(f"Debug   : {debug}")
    print("-" * 60)

    with open(output_path, "w", encoding="utf-8") as f:
        while generated < count:
            incident = random.choice(INCIDENT_TYPES)
            style = random.choice(SOURCE_STYLES)
            severity = random.choice(SEVERITIES)
            location = random.choice(JAPANESE_PREFECTURES)

            print(f"[{generated + 1}/{count}] {incident} | {style} | {severity} | {location}")
            prompt = get_prompt(incident, style, location, severity)

            parsed = None

            for attempt in range(1, max_retries + 1):
                try:
                    raw = call_ollama(prompt, model=model, timeout=timeout)

                    if debug:
                        print(f"  RAW OUTPUT: {raw[:400]}")

                    parsed = parse_response(raw)

                    if parsed:
                        parsed = normalize_parsed(
                            parsed,
                            expected_incident=incident,
                            expected_severity=severity,
                            expected_style=style,
                        )

                    if parsed and is_valid_parsed(parsed):
                        break

                    print(f"  ↳ Attempt {attempt}/{max_retries}: validation failed")

                except requests.exceptions.Timeout:
                    print(f"  ↳ Attempt {attempt}/{max_retries}: timeout after {timeout}s")
                except requests.RequestException as e:
                    print(f"  ↳ Attempt {attempt}/{max_retries}: request error: {e}")

                time.sleep(2)

            if not parsed or not is_valid_parsed(parsed):
                failed += 1
                print(f"  ↳ Skipped. Total failures: {failed}")
                continue

            sample = {
                "sample_id": f"syn-jp-{uuid.uuid4().hex[:10]}",
                "source_type": style,
                "raw_text": parsed["raw_text"],
                "label": parsed["label"],
                "annotator": f"synthetic_{model.replace(':', '_')}",
                "is_synthetic": True,
                "language": parsed["language"],
                "location_hint": location,
                "ambiguity_score": parsed["ambiguity_score"],
                "notes": f"style={style}",
            }

            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            f.flush()
            generated += 1

    print(f"\nGeneration complete. Generated: {generated}, Failed: {failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--output", type=str, default="data/synthetic/synthetic_japan.jsonl")
    parser.add_argument("--model", type=str, default="qwen3:8b")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--debug", action="store_true", help="Print raw model output for each sample")
    args = parser.parse_args()
    main(args.count, args.output, args.model, args.timeout, args.debug)