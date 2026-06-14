from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import httpx
import sys
import os
import json
# Ensure repository root is on sys.path so shared modules can be imported
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from shared.orchestrator import PipelineOrchestrator
from .demo_data import (
    get_demo_replay, get_demo_simulation, get_demo_incident, get_demo_zones, 
    get_demo_allocation, get_demo_resources, get_demo_routes_display,
    get_demo_prediction, get_demo_learning, get_demo_timeline, get_demo_dashboard,
    get_demo_gis, DEMO_INCIDENT_ID
)
from fastapi.responses import StreamingResponse
from app.services.replay_store import save_stages, get_stages, load_all, init_db
import asyncio

router = APIRouter(prefix="/api/v1/command", tags=["command"])

# initialize sqlite-backed store
init_db()
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() in ('1','true','yes')
# Per-incident async queues for server-sent events
EVENT_QUEUES: Dict[str, asyncio.Queue] = {}



class ProcessRequest(BaseModel):
    incident_id: Optional[str] = None
    detection_payload: Optional[Dict[str, Any]] = None


class SimulateRequest(BaseModel):
    incident_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    incident_type: Optional[str] = "Flood"
    steps: Optional[int] = 4


@router.get("/incidents")
async def list_incidents(limit: int = 50):
    """Proxy to Detection Agent incidents list."""
    try:
        # Allow overriding agent hostnames via environment for Docker Compose
        DETECTION_HOST = os.getenv("DETECTION_HOST", "localhost:8000")
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"http://{DETECTION_HOST}/api/v1/incidents?limit={limit}")
            res.raise_for_status()
            return res.json()
    except Exception as e:
        # If detection agent is unavailable, return local sample incidents for demo
        try:
            samples = await list_samples()
            return {"items": samples}
        except Exception:
            raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {e}")


@router.get("/samples")
async def list_samples():
    """Return sample detection events from the repository data folder."""
    try:
        samples_path = os.path.join(repo_root, 'data', 'sample_detection_events.json')
        if not os.path.exists(samples_path):
            raise HTTPException(status_code=404, detail="Samples not found")
        with open(samples_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        # expect a list; wrap if needed
        if isinstance(data, dict) and 'samples' in data:
            return data['samples']
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load samples: {e}")


@router.get("/incident/{incident_id}")
async def get_incident_state(incident_id: str):
    """Fetch detection incident and run orchestrator to build full incident state."""
    try:
        DETECTION_HOST = os.getenv("DETECTION_HOST", "localhost:8000")
        async with httpx.AsyncClient(timeout=20.0) as client:
            # fetch detection incident
            det = await client.get(f"http://{DETECTION_HOST}/api/v1/incidents/{incident_id}")
            if det.status_code != 200:
                raise HTTPException(status_code=det.status_code, detail="Detection incident not found")
            detection = det.json()

        if DEMO_MODE:
            # return preloaded demo incident when demo mode active
            replay = get_demo_replay()
            # save to sqlite store for replay convenience
            save_stages(replay['incident_id'], replay['stages'])
            # find final
            final = [s for s in replay['stages'] if s.get('stage') == 'final']
            return final[0]['output'] if final else replay
        orchestrator = PipelineOrchestrator()
        incident_state = await orchestrator.process_incident(detection)
        # store for replay (sqlite)
        save_stages(incident_id, [{"stage": "final", "output": incident_state}])
        return incident_state
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {e}")


@router.post("/process")
async def process_incident(req: ProcessRequest):
    """Process a detection payload or an existing incident id through the pipeline."""
    try:
        if req.incident_id and not req.detection_payload:
            # fetch detection from detection agent; if unreachable, fall back to local sample file
            DETECTION_HOST = os.getenv("DETECTION_HOST", "localhost:8000")
            detection = None
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    det = await client.get(f"http://{DETECTION_HOST}/api/v1/incidents/{req.incident_id}")
                    det.raise_for_status()
                    detection = det.json()
            except Exception:
                # Attempt to load from local samples
                try:
                    samples = await list_samples()
                    # samples may be a list or dict, handle both
                    if isinstance(samples, dict) and 'samples' in samples:
                        samples_list = samples['samples']
                    else:
                        samples_list = samples
                    for s in samples_list:
                        if s.get('incident_id') == req.incident_id:
                            detection = s
                            break
                except Exception:
                    detection = None
            if detection is None:
                raise HTTPException(status_code=404, detail=f"Detection incident {req.incident_id} not found")
        elif req.detection_payload:
            detection = req.detection_payload
        else:
            raise HTTPException(status_code=400, detail="Provide incident_id or detection_payload")

        orchestrator = PipelineOrchestrator()

        # create event queue for this processing run so clients can subscribe
        incident_key = detection.get("incident_id") or f"local_{int(asyncio.get_event_loop().time())}"
        q = asyncio.Queue()
        EVENT_QUEUES[incident_key] = q

        async def on_stage(stage: str, output: Dict[str, Any]):
            payload = {"incident_id": incident_key, "stage": stage, "output": output}
            try:
                await q.put(payload)
            except Exception:
                pass

        try:
            # If demo mode, short-circuit to demo data
            if DEMO_MODE:
                replay = get_demo_replay()
                incident_id = replay['incident_id']
                save_stages(incident_id, replay['stages'])
                # push stages to queue
                try:
                    for s in replay['stages']:
                        await q.put({"incident_id": incident_id, "stage": s.get('stage'), "output": s.get('output')})
                    await q.put(None)
                except Exception:
                    pass
                final = [s for s in replay['stages'] if s.get('stage') == 'final']
                return {"incident_id": incident_id, "state": final[0]['output'] if final else replay}
            # Attempt full orchestrator run with live stage callback
            incident_state = await orchestrator.process_incident(detection, on_stage=on_stage)
            incident_id = incident_state.get("incident_id", incident_key)
            # Store a single final snapshot for replay (sqlite)
            save_stages(incident_id, [{"stage": "final", "output": incident_state}])
            # push final event and close stream
            try:
                await q.put({"incident_id": incident_id, "stage": "final", "output": incident_state})
                await q.put(None)
            except Exception:
                pass
            return {"incident_id": incident_id, "state": incident_state}
        except Exception as exc:
            # Log exception for debugging so we can diagnose why orchestrator failed
            try:
                import traceback
                traceback.print_exc()
            except Exception:
                pass
            # If external agents are unavailable, return a safe partial state
            incident_id = detection.get("incident_id", f"local_{int(asyncio.get_event_loop().time())}")
            fallback_state = {
                **detection,
                "incident_id": incident_id,
                "pipeline_stage": "partial",
                "severity": detection.get("severity", "Medium"),
                "gis_output": {
                    "affected_radius_km": 5.0,
                    "center": {"latitude": detection.get("latitude"), "longitude": detection.get("longitude")},
                },
                "resource_output": {"resources": [{"id": "local_team_1", "type": "medical", "location": {"latitude": detection.get("latitude"), "longitude": detection.get("longitude")}}]},
                "route_output": {"routes": []},
                "communication_output": {"alerts": [{"target_audience": "Public", "language": "en", "message": f"Detected {detection.get('incident_type')} at {detection.get('location')}"}]},
                "prediction_output": {"forecast": "unknown"},
                "learning_output": None,
            }

            stages = [
                {"stage": "assessment", "output": {"severity": fallback_state.get("severity")}},
                {"stage": "gis", "output": fallback_state.get("gis_output")},
                {"stage": "resource", "output": fallback_state.get("resource_output")},
                {"stage": "route", "output": fallback_state.get("route_output")},
                {"stage": "communication", "output": fallback_state.get("communication_output")},
            ]
            save_stages(incident_id, stages)
            # push fallback stages to any open queue and close
            try:
                q = EVENT_QUEUES.get(incident_id)
                if q:
                    for s in stages:
                        await q.put({"incident_id": incident_id, "stage": s.get('stage'), "output": s.get('output')})
                    await q.put(None)
            except Exception:
                pass
            return {"incident_id": incident_id, "state": fallback_state, "warning": "Partial result: external agents unreachable"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")


@router.get("/replay/{incident_id}")
async def get_replay(incident_id: str):
    """Return stored replay stages for an incident."""
    stages = get_stages(incident_id)
    if not stages:
        if DEMO_MODE and incident_id.startswith('chennai'):
            # provide demo replay
            replay = get_demo_replay()
            save_stages(replay['incident_id'], replay['stages'])
            return replay
        raise HTTPException(status_code=404, detail="Replay not found for incident")
    return {"incident_id": incident_id, "stages": stages}


@router.get('/stream/{incident_id}')
async def stream_incident(incident_id: str):
    """Server-Sent Events stream for pipeline stages of an incident."""
    q = EVENT_QUEUES.get(incident_id)
    if q is None:
        # create a queue so callers can still wait for future events
        q = asyncio.Queue()
        EVENT_QUEUES[incident_id] = q

    async def event_generator():
        try:
            while True:
                item = await q.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            EVENT_QUEUES.pop(incident_id, None)

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@router.post("/simulate")
async def simulate(req: SimulateRequest):
    """Return a simple expansion time-series (radii) for a digital twin animation."""
    try:
        # Determine center
        if req.incident_id:
            async with httpx.AsyncClient(timeout=10.0) as client:
                det = await client.get(f"http://localhost:8000/api/v1/incidents/{req.incident_id}")
                det.raise_for_status()
                incident = det.json()
            lat = incident.get("latitude")
            lon = incident.get("longitude")
            itype = incident.get("incident_type", req.incident_type)
        else:
            lat = req.latitude
            lon = req.longitude
            itype = req.incident_type

        if lat is None or lon is None:
            raise HTTPException(status_code=400, detail="Provide incident_id or latitude/longitude")

        # Get base zones from disaster agents or demo data
        if DEMO_MODE:
            zdata = get_demo_zones()
        else:
            DISASTER_HOST = os.getenv("DISASTER_HOST", "localhost:8002")
            async with httpx.AsyncClient(timeout=20.0) as client:
                zones_req = {
                    "incident_id": req.incident_id or "sim_local",
                    "incident_type": itype,
                    "latitude": lat,
                    "longitude": lon,
                    "hazard_severity": "Medium",
                }
                zres = await client.post(f"http://{DISASTER_HOST}/api/v1/gis/zones", json=zones_req)
                zres.raise_for_status()
                zdata = zres.json()

        base_r = zdata.get("affected_radius_km", 5.0)
        steps = req.steps or 4
        timeseries = []
        for i in range(steps):
            factor = 1.0 + (i * 0.3)
            timeseries.append({
                "t": i,
                "radius_km": round(base_r * factor, 3),
                "center": {"latitude": lat, "longitude": lon},
            })

        return {"incident_id": req.incident_id or "sim_local", "timeseries": timeseries}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")


@router.post('/demo/create')
async def create_demo(city: str = 'chennai'):
    """Create a fully prepared demo incident (zones, routes, allocations) and store replay."""
    try:
        # build a demo detection payload
        city = (city or 'chennai').lower()
        demo_map = {
            'chennai': {'latitude': 13.0827, 'longitude': 80.2707, 'incident_id': 'chennai_demo_001', 'incident_type': 'Flood', 'severity': 'High', 'affected_population': 2500},
            'delhi': {'latitude': 28.6139, 'longitude': 77.2090, 'incident_id': 'delhi_demo_001', 'incident_type': 'Flood', 'severity': 'High', 'affected_population': 1200},
        }
        det = demo_map.get(city, demo_map['chennai'])

        # In demo mode, return prebuilt demo assets for Chennai
        if DEMO_MODE:
            replay = get_demo_replay()
            save_stages(replay['incident_id'], replay['stages'])
            final = [s for s in replay['stages'] if s.get('stage') == 'final']
            return {"incident_id": replay['incident_id'], "state": final[0]['output'] if final else replay}
        orchestrator = PipelineOrchestrator()
        # run the orchestrator which will call mock services to prepare zones, routes, and allocations
        state = await orchestrator.process_incident(det)
        incident_id = state.get('incident_id') or det.get('incident_id')
        save_stages(incident_id, [{"stage": "final", "output": state}])
        return {"incident_id": incident_id, "state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo creation failed: {e}")



@router.get("/demo")
async def get_demo():
    """Return the complete DEMO-CHENNAI-001 incident with all precomputed data."""
    replay = get_demo_replay()
    save_stages(replay['incident_id'], replay['stages'])
    final = [s for s in replay['stages'] if s.get('stage') == 'final']
    return {
        "incident_id": replay['incident_id'],
        "state": final[0]['output'] if final else replay,
        "stages": replay['stages']
    }


@router.get("/demo/incident")
async def get_demo_incident_endpoint():
    """Return just the incident data for DEMO-CHENNAI-001."""
    return get_demo_incident()


@router.get("/demo/quick")
async def get_demo_quick():
    """Quick demo endpoint - returns minimal preloaded data for instant UI load."""
    incident = get_demo_incident()
    return {
        "incident": incident,
        "gis": get_demo_gis(),
        "resources": get_demo_resources(),
        "allocation": get_demo_allocation(),
        "routes": get_demo_routes_display(),
        "prediction": get_demo_prediction(),
        "learning": get_demo_learning(),
        "timeline": get_demo_timeline(),
        "demo_mode": True
    }

