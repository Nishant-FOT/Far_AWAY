import urllib.request, json

def check(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            j = json.load(r)
            coords = j['routes'][0]['geometry']['coordinates']
            return {'ok': True, 'count': len(coords)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

center = (13.15, 80.29)
res = (13.18, 80.27)
local = f"http://localhost:5000/route/v1/driving/{res[1]},{res[0]};{center[1]},{center[0]}?overview=full&geometries=geojson"
public = f"https://router.project-osrm.org/route/v1/driving/{res[1]},{res[0]};{center[1]},{center[0]}?overview=full&geometries=geojson"
print('local ->', check(local))
print('public->', check(public))
