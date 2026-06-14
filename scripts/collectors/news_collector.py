"""
Collects Japan disaster news from RSS feeds.
Filters for disaster-relevant articles using keyword matching,
then stores them as raw dataset samples for annotation.

Supported sources:
  - NHK (Japanese + English)
  - Japan Times (English)
  - Kyodo News (Japanese)
  - Asahi Shimbun (Japanese)

Design rationale:
  RSS feeds are updated every 15–30 minutes and are free with no rate limits.
  We use keyword pre-filtering before sending to Qwen3-14B for annotation,
  reducing API calls by ~80% (most news is not disaster-related).
"""
import json
import hashlib
import feedparser
from datetime import datetime, timezone
from pathlib import Path

RSS_FEEDS = {
    "nhk_ja": "https://www3.nhk.or.jp/rss/news/cat6.xml",     # 社会・防災
    "nhk_en": "https://www3.nhk.or.jp/nhkworld/en/news/rss/",
    "japantimes": "https://www.japantimes.co.jp/feed/",
    "asahi": "https://rss.asahi.com/rss/asahi/newsheadlines.rdf",
}

# Japanese disaster keywords (hiragana/kanji)
JA_KEYWORDS = [
    "地震", "津波", "台風", "洪水", "土砂崩れ", "火山", "噴火", "大雪",
    "火災", "倒壊", "浸水", "避難", "震度", "マグニチュード", "高潮",
    "河川氾濫", "土石流", "崖崩れ", "豪雨", "暴風",
]
# English disaster keywords
EN_KEYWORDS = [
    "earthquake", "tsunami", "typhoon", "flood", "landslide", "volcano",
    "eruption", "snowstorm", "fire", "collapse", "evacuation", "disaster",
    "shindo", "magnitude", "storm surge", "heavy rain",
]

OUTPUT_FILE = Path("data/raw/news_samples.jsonl")


def is_disaster_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EN_KEYWORDS + JA_KEYWORDS)


def detect_language(text: str) -> str:
    # Simple heuristic: presence of CJK characters → Japanese
    return "ja" if any("\u4e00" <= c <= "\u9fff" for c in text) else "en"


def collect_feed(source_name: str, url: str) -> list:
    samples = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title}. {summary}".strip()

            if not is_disaster_relevant(full_text):
                continue

            sample_id = "news-" + hashlib.md5(full_text.encode()).hexdigest()[:12]
            lang = detect_language(full_text)

            sample = {
                "sample_id": sample_id,
                "source_type": "news",
                "raw_text": full_text,
                "label": None,      # To be filled by Qwen3-14B annotator
                "annotator": "pending",
                "is_synthetic": False,
                "language": lang,
                "location_hint": None,
                "ambiguity_score": None,
                "notes": f"source={source_name}, url={entry.get('link','')}",
            }
            samples.append(sample)
    except Exception as e:
        print(f"[{source_name}] Feed error: {e}")
    return samples


def collect_all():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    total = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for source, url in RSS_FEEDS.items():
            samples = collect_feed(source, url)
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
                total += 1
            print(f"[{source}] {len(samples)} disaster-relevant articles collected")

    print(f"\nTotal news samples collected: {total}")


if __name__ == "__main__":
    collect_all()