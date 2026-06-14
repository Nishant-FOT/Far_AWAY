


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
