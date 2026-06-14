from disaster_detection_agent.app.incidents.builder import build_incident


def test_build_incident():
    inc = build_incident({"id": "123"})
    assert inc.id == "123"
