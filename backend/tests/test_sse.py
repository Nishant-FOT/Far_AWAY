import json
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.api import command_router


def test_streaming_endpoint():
    incident_id = 'test_stream_1'
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    q = asyncio.Queue()
    # prefill a couple of events and a terminator
    loop.run_until_complete(q.put({"incident_id": incident_id, "stage": "assessment", "output": {"ok": True}}))
    loop.run_until_complete(q.put({"incident_id": incident_id, "stage": "gis", "output": {"ok": True}}))
    loop.run_until_complete(q.put(None))

    command_router.EVENT_QUEUES[incident_id] = q

    client = TestClient(app)
    with client.stream('GET', f'/api/v1/command/stream/{incident_id}') as response:
        assert response.status_code == 200
        lines = []
        for line in response.iter_lines():
            if not line:
                continue
            text = line.decode('utf-8') if isinstance(line, bytes) else line
            if text.startswith('data: '):
                payload = json.loads(text[len('data: '):])
                lines.append(payload)
        # we expect two events
        assert len(lines) >= 2
        assert any(e['stage'] == 'assessment' for e in lines)
        assert any(e['stage'] == 'gis' for e in lines)
