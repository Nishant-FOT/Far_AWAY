from disaster_detection_agent.app.pipeline.orchestrator import Orchestrator


def test_orchestrator_empty():
    o = Orchestrator([])
    assert o.run({}) == {}
