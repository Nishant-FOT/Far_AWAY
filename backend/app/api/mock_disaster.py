from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
import math
import os
import json
import httpx

router = APIRouter(prefix="/api/v1/mock", tags=["mock_disaster"])
router2 = APIRouter(prefix="/api/v1", tags=["mock_disaster_public"])

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

# Simple in-repo resource lists for demo cities
CITY_RESOURCES = {
    "delhi": [
        {"id": "AIIMS", "name": "AIIMS Hospital", "type": "hospital", "latitude": 28.5672, "longitude": 77.2100},
        {"id": "RD", "name": "Red Cross Shelter", "type": "shelter", "latitude": 28.5450, "longitude": 77.2105},
        {"id": "NDH", "name": "North District Hospital", "type": "hospital", "latitude": 28.7000, "longitude": 77.1000},
    ],
    "tokyo": [
        {"id": "TGW", "name": "Tokyo General Hospital", "type": "hospital", "latitude": 35.6762, "longitude": 139.6503},
        {"id": "TK_SHEL", "name": "Shinjuku Shelter", "type": "shelter", "latitude": 35.6938, "longitude": 139.7034},
    ],
    "chennai": [
        {"id": "CMC", "name": "Chennai Medical Center", "type": "hospital", "latitude": 13.0827, "longitude": 80.2707},
        {"id": "CH_SHEL", "name": "Adyar Shelter", "type": "shelter", "latitude": 13.0100, "longitude": 80.2400},
    ],
    "kerala": [
        {"id": "KCH", "name": "Kochi Hospital", "type": "hospital", "latitude": 9.9312, "longitude": 76.2673},
        {"id": "KL_SHEL", "name": "Cochin Shelter", "type": "shelter", "latitude": 9.9667, "longitude": 76.2833},
    ],
}


# Expand CITY_RESOURCES with synthetic nodes to make demos more realistic
def _expand_resources():
    for city, lst in list(CITY_RESOURCES.items()):
        if len(lst) >= 20:
            continue
        # use first known point as center
        if len(lst) == 0:
            continue
        center = lst[0]
        cx = center['latitude']
        cy = center['longitude']
        gen = []
        types = ['hospital', 'fire_station', 'ambulance_base', 'shelter', 'helipad']
        for i in range(1, 31):
            t = types[i % len(types)]
            lat = cx + ((i % 5) - 2) * 0.01 + (i/10000)
            lon = cy + (((i+2) % 5) - 2) * 0.01 + (i/10000)
            gid = f"{city[:3].upper()}_{t[:3].upper()}_{i}"
            name = f"{city.title()} {t.replace('_',' ').title()} {i}"
            gen.append({"id": gid, "name": name, "type": t if t!='ambulance_base' else 'ambulance', "latitude": round(lat,6), "longitude": round(lon,6)})
        # prepend generated nodes so nearest nodes are near center
        CITY_RESOURCES[city] = gen + lst


_expand_resources()


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def circle_geojson(center_lat, center_lon, radius_km, level='CRITICAL', color='red'):
    # approximate circle as polygon with 24 points
    points = []
    for i in range(24):
        theta = 2 * math.pi * i / 24
        dx = (radius_km/111.32) * math.cos(theta)
        dy = (radius_km/111.32) * math.sin(theta) / math.cos(math.radians(center_lat))
        lat = center_lat + dy
        lon = center_lon + dx
        points.append([lat, lon])
    # close polygon
    points.append(points[0])
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [points]},
        "properties": {"level": level, "color": color}
    }


@router.post('/gis/analyze')
async def analyze_gis(payload: Dict[str, Any]):
    lat = payload.get('latitude')
    lon = payload.get('longitude')
    severity = payload.get('hazard_severity', 'Medium')
    # base radius by severity
    base = 5.0
    if severity and severity.lower().startswith('high'):
        base = 10.0
    elif severity and severity.lower().startswith('low'):
        base = 2.5
    # simple risk probability
    risk = 0.6 if severity == 'Medium' else 0.85 if severity == 'High' else 0.3
    return {"affected_radius_km": base, "risk_probability": risk, "priority_zone": "CRITICAL" if risk>0.7 else "MODERATE", "center": {"latitude": lat, "longitude": lon}, "infrastructure_vulnerability": "Medium", "resource_availability": "Medium"}


@router2.post('/gis/analyze')
async def analyze_gis_public(payload: Dict[str, Any]):
    return await analyze_gis(payload)


@router.post('/gis/zones')
async def gis_zones(payload: Dict[str, Any]):
    lat = payload.get('latitude')
    lon = payload.get('longitude')
    severity = payload.get('hazard_severity', 'Medium')
    # Allow explicit demo radii override for nicer visualizations
    demo_override = payload.get('demo_zones', False)
    if demo_override:
        # critical 20km, moderate 30km, safe 60km
        critical_r = 20.0
        moderate_r = 30.0
        safe_r = 60.0
    else:
        base = 5.0
        if severity and severity.lower().startswith('high'):
            base = 10.0
        critical_r = base
        moderate_r = base * 1.6
        safe_r = base * 2.8

    critical = circle_geojson(lat, lon, critical_r, 'CRITICAL', 'red')
    moderate = circle_geojson(lat, lon, moderate_r, 'MODERATE', 'orange')
    safe = circle_geojson(lat, lon, safe_r, 'SAFE', 'green')
    fc = {"type": "FeatureCollection", "features": [critical, moderate, safe]}
    return {"incident_id": payload.get('incident_id', 'local'), "affected_radius_km": critical_r, "zones_geojson": fc}


@router2.post('/gis/zones')
async def gis_zones_public(payload: Dict[str, Any]):
    return await gis_zones(payload)


@router.get('/gis/resources')
async def list_resources(city: str = None):
    cname = (city or '').lower()
    if not cname:
        # return all resources flattened
        out = []
        for lst in CITY_RESOURCES.values():
            out.extend(lst)
        return {"resources": out}
    out = CITY_RESOURCES.get(cname, [])
    return {"resources": out}


@router2.get('/gis/resources')
async def list_resources_public(city: str = None):
    return await list_resources(city)


@router.post('/route/optimize')
async def optimize_route(payload: Dict[str, Any]):
    incident_lat = payload.get('incident_lat') or payload.get('latitude')
    incident_lon = payload.get('incident_lon') or payload.get('longitude')
    available = payload.get('available_resources', [])
    itype = (payload.get('incident_type') or '').lower()

    # build candidate nodes from CITY_RESOURCES
    candidates = []
    for lst in CITY_RESOURCES.values():
        for r in lst:
            d = haversine(incident_lat, incident_lon, r['latitude'], r['longitude'])
            candidates.append({**r, 'distance_km': round(d,3)})
    candidates.sort(key=lambda x: x['distance_km'])

    # speed assumptions (km/h) - tuned for demo
    speeds = {
        'ambulance': 65.0,
        'fire_station': 50.0,
        'firetruck': 45.0,
        'boat': 25.0,
        'helipad': 220.0,
        'helicopter': 220.0,
        'ambulance_base': 65.0,
        'hospital': 60.0,
        'shelter': 40.0,
        'default': 45.0,
    }

    def estimate_time_km(distance_km, rtype):
        sp = speeds.get(rtype, speeds['default'])
        if sp <= 0:
            sp = speeds['default']
        hours = distance_km / sp
        return int(hours * 60)

    routes = []
    routes = []
    # create routes for nearest candidates up to 8; prefer local OSRM if available, otherwise fall back to synthetic multi-point polylines
    async def make_route_path(src_lat, src_lon, dst_lat, dst_lon):
        # prefer an OSRM instance configured via OSRM_HOST env var (service name in compose)
        osrm_host = os.getenv('OSRM_HOST', '127.0.0.1:5000')
        try:
            osrm_url = f"http://{osrm_host}/route/v1/driving/{src_lon},{src_lat};{dst_lon},{dst_lat}?overview=full&geometries=geojson"
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(osrm_url)
                if resp.status_code == 200:
                    j = resp.json()
                    if j.get('routes') and len(j['routes'])>0:
                        coords = j['routes'][0].get('geometry', {}).get('coordinates', [])
                        # convert [lon,lat] -> [lat,lon]
                        path = [[c[1], c[0]] for c in coords]
                        if len(path) >= 2:
                            return path
        except Exception:
            # OSRM not available or failed - fall back to synthetic
            pass

        # synthetic fallback: denser, road-like waypoints using biased interpolation
        pts = []
        steps = max(6, int(haversine(src_lat, src_lon, dst_lat, dst_lon) * 10))
        for i in range(steps + 1):
            t = i / steps
            # biased interpolation that prefers axis-aligned movement (simulate following roads)
            weight = 0.6
            lat_interp = src_lat + (dst_lat - src_lat) * (t ** weight)
            lon_interp = src_lon + (dst_lon - src_lon) * (t ** (1/weight))
            # introduce small systematic curvature and snapping to grid to look like roads
            curve = 0.0009 * math.sin(t * math.pi * 2.5)
            snap_lat = round(lat_interp, 5)
            snap_lon = round(lon_interp, 5)
            pts.append([round(snap_lat + curve, 6), round(snap_lon - curve, 6)])
        return pts

    for c in candidates[:8]:
        rtype = c.get('type', '').lower() or 'default'
        travel_min = estimate_time_km(c['distance_km'], rtype)
        path = await make_route_path(c['latitude'], c['longitude'], incident_lat, incident_lon)
        routes.append({
            "resource_id": c['id'],
            "resource_name": c.get('name'),
            "resource_type": c.get('type'),
            "distance_km": c['distance_km'],
            "eta_min": travel_min,
            "path_coords": path
        })

    # determine a safe zone target: use incident zones if provided
    safe_point = None
    zones = payload.get('zones')
    if zones and isinstance(zones, dict) and zones.get('features'):
        # pick the SAFE polygon if present
        for f in zones.get('features'):
            if f.get('properties', {}).get('level') == 'SAFE':
                coords = f.get('geometry', {}).get('coordinates', [])
                if coords and isinstance(coords, list) and coords[0]:
                    # centroid approx: average first ring
                    ring = coords[0]
                    lat = sum([p[0] for p in ring]) / len(ring)
                    lon = sum([p[1] for p in ring]) / len(ring)
                    safe_point = [lat, lon]
                    break

    if not safe_point:
        # fallback safe point offset
        safe_point = [incident_lat + 0.02, incident_lon + 0.02]

    # fastest escape path: compute a more realistic road-like escape path with waypoints
    escape_distance = haversine(incident_lat, incident_lon, safe_point[0], safe_point[1])
    escape_time_min = estimate_time_km(escape_distance, 'default')
    async def make_road_path(a, b):
        lat1, lon1 = a
        lat2, lon2 = b
        # attempt OSRM for escape route
        osrm_host = os.getenv('OSRM_HOST', '127.0.0.1:5000')
        try:
            osrm_url = f"http://{osrm_host}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(osrm_url)
                if resp.status_code == 200:
                    j = resp.json()
                    if j.get('routes') and len(j['routes'])>0:
                        coords = j['routes'][0].get('geometry', {}).get('coordinates', [])
                        return [[c[1], c[0]] for c in coords]
        except Exception:
            pass
        # synthetic road-like path with multiple waypoints and slight curvature
        pts = []
        dist_km = haversine(lat1, lon1, lat2, lon2)
        steps = max(8, int(dist_km * 8))
        for i in range(steps + 1):
            t = i / steps
            # create gentle curvature and a small lateral offset to mimic following roads
            lat_interp = lat1 + (lat2 - lat1) * t + 0.0015 * math.sin(t * math.pi * 2)
            lon_interp = lon1 + (lon2 - lon1) * t + 0.0015 * math.cos(t * math.pi * 2)
            # snap to 5-decimal grid to produce straighter segments
            pts.append([round(lat_interp, 6), round(lon_interp, 6)])
        return pts

    escape_path = await make_road_path([incident_lat, incident_lon], safe_point)
    escape = {"path_coords": escape_path, "type": "escape", "distance_km": round(escape_distance,3), "eta_min": escape_time_min}

    # Evacuation planning for people in critical zone
    evacuation = {}
    if itype and 'flood' in itype:
        # prefer boats and helicopters + driving
        # compute nearest helipad if any
        helipads = [c for c in candidates if c.get('type') in ('helipad', 'helipad')]
        nearest_helipad = helipads[0] if helipads else None
        # walking and driving estimates to safe_point
        walk_speed = 5.0
        drive_speed = 40.0
        walk_min = int((escape_distance / walk_speed) * 60)
        drive_min = int((escape_distance / drive_speed) * 60)
        best_mode = 'drive' if drive_min <= walk_min else 'walk'
        best_eta = min(walk_min, drive_min)
        # helicopter option
        heli_option = None
        if nearest_helipad and len(helipads) > 0:
            # time to helipad + flight to safe_point (straight-line)
            to_helipad_km = haversine(incident_lat, incident_lon, nearest_helipad['latitude'], nearest_helipad['longitude'])
            heli_flight_km = haversine(nearest_helipad['latitude'], nearest_helipad['longitude'], safe_point[0], safe_point[1])
            heli_total_min = int((to_helipad_km / speeds.get('helipad',220.0) + heli_flight_km / speeds.get('helicopter',220.0)) * 60) + 10
            heli_option = {'mode': 'helicopter', 'eta_min': heli_total_min, 'pickup_at': [nearest_helipad['latitude'], nearest_helipad['longitude']], 'helipad_id': nearest_helipad.get('id')}
            if heli_total_min < best_eta:
                best_mode = 'helicopter'
                best_eta = heli_total_min

        evacuation = {
            'safe_point': safe_point,
            'escape_distance_km': round(escape_distance,3),
            'best_mode': best_mode,
            'best_eta_min': best_eta,
            'walk_eta_min': walk_min,
            'drive_eta_min': drive_min,
            'helicopter_option': heli_option,
        }
    else:
        # general incidents: suggest drive/walk
        walk_speed = 5.0
        drive_speed = 40.0
        walk_min = int((escape_distance / walk_speed) * 60)
        drive_min = int((escape_distance / drive_speed) * 60)
        evacuation = {'safe_point': safe_point, 'escape_distance_km': round(escape_distance,3), 'best_mode': 'drive' if drive_min<=walk_min else 'walk', 'best_eta_min': min(walk_min, drive_min), 'walk_eta_min': walk_min, 'drive_eta_min': drive_min}

    return {"routes": routes, "escape": escape, "evacuation_plan": evacuation}


@router2.post('/route/optimize')
async def optimize_route_public(payload: Dict[str, Any]):
    return await optimize_route(payload)


@router2.post('/resource/allocate')
async def resource_allocate_public(payload: Dict[str, Any]):
    # debug log incoming payload
    try:
        print("[mock_disaster] resource_allocate_public called with:", payload)
    except Exception:
        pass
    # allocate resources based on incident type and affected population
    lat = payload.get('latitude') or payload.get('incident_lat')
    lon = payload.get('longitude') or payload.get('incident_lon')
    itype = (payload.get('incident_type') or '').lower()
    affected = int(payload.get('affected_population') or payload.get('population') or 0)

    # Build candidate pool
    candidates = []
    for lst in CITY_RESOURCES.values():
        for r in lst:
            d = haversine(lat, lon, r['latitude'], r['longitude'])
            candidates.append({**r, 'distance_km': round(d,3)})
    candidates.sort(key=lambda x: x['distance_km'])

    # Resource demand model (updated heuristics)
    demand = {}
    if 'flood' in itype or 'water' in itype:
        # floods need many boats, food, medical support and helicopters for critical patients
        demand = {
            'boats': max(1, (affected + 24) // 25),
            'helicopters': max(0, (affected + 199) // 200),
            'food_kits': affected,
            'medical_teams': max(1, (affected + 99) // 100),
            'ambulances': max(1, (affected + 99) // 100)
        }
    elif 'fire' in itype:
        # fires require fast firetrucks and ambulances proportional to casualties
        demand = {
            'firetrucks': max(1, (affected + 49) // 50),
            'ambulances': max(1, (affected + 49) // 50),
            'rescue_squads': max(1, (affected + 99) // 100)
        }
    else:
        # default mixed demand
        demand = {
            'ambulances': max(1, (affected + 99) // 100),
            'medical_teams': max(1, (affected + 199) // 200),
            'shelters': max(1, (affected + 499) // 500)
        }

    # Allocate nearest resources to meet demand where possible
    allocations = []
    # simple mapping from resource types to candidate types
    type_map = {
        'hospital': ['ambulance', 'medical_teams'],
        'shelter': ['shelters'],
    }

    # assign generic teams from nearest nodes
    for i, c in enumerate(candidates[:20]):
        alloc = {"resource_id": c['id'], "name": c.get('name'), "type": c.get('type'), "distance_km": c['distance_km'], "assigned": {}}
        # heuristics: assign ambulances/firetrucks based on distance and availability
        if 'ambulance' in c.get('id', '').lower() or c.get('type') == 'hospital' or 'hospital' in c.get('name', '').lower():
            alloc['assigned']['ambulances'] = min( max(1, affected//500 - i), 3 ) if affected>0 else 0
            alloc['assigned']['medical_teams'] = min( max(0, affected//800 - i), 2 )
        if 'shelter' in c.get('type', '') or 'shelter' in c.get('name', '').lower():
            alloc['assigned']['shelters'] = min( max(1, affected//1000 - i), 5 )
        allocations.append(alloc)

    allocation_plan = {
        'demand': demand,
        'allocations': allocations[:10],
        'total_candidates': len(candidates),
        'estimated_response_time_min': 15
    }
    return allocation_plan


@router2.post('/communication/generate-alerts')
async def generate_alerts_public(payload: Dict[str, Any]):
    loc = payload.get('location')
    if not loc:
        lat = payload.get('latitude')
        lon = payload.get('longitude')
        loc = f"{lat},{lon}"
    message = f"Detected {payload.get('incident_type')} at {loc}."
    return {"alerts": [{"target_audience": "Public", "language": "en", "message": message}]}


@router2.post('/predict')
async def predict_public(payload: Dict[str, Any]):
    return {"forecast": "stable", "confidence": 0.5}


@router2.post('/learning/analyze')
async def learning_public(payload: Dict[str, Any]):
    return {"learning": "no-op", "notes": "demo data"}
