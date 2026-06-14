import urllib.request, json
url='http://localhost:8100/api/v1/command/replay/chennai_demo_collapse_001'
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        j = json.load(r)
        routes = None
        for s in j.get('stages',[]):
            if s.get('stage')=='route':
                routes = s.get('output', {}).get('routes')
                break
        if not routes:
            routes = j.get('stages',[]) and j['stages'][-1].get('output',{}).get('routes')
        print(json.dumps([{'resource_id': r.get('resource_id'), 'distance_km': r.get('distance_km'), 'pts': len(r.get('path_coords',[]))} for r in (routes or [])], indent=2))
except Exception as e:
    print('ERR', e)
