from disaster_detection_agent.app.ingestion.normalizer import normalize


def test_normalize():
    raw = {"text": " Hello ", "source": "test"}
    out = normalize(raw)
    assert out["text"] == "Hello"
