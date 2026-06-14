#!/usr/bin/env python3
"""Generate real OSRM routes for demo incident."""
import json
import time
import httpx

INCIDENT_LAT = 12.812169
INCIDENT_LNG = 80.230532

HOSPITALS = [
    {"name": "Apollo Speciality Hospital Nungambakkam", "lat": 13.0500, "lng": 80.2300},
    {"name": "Sri Ramakrishna Hospital", "lat": 13.0200, "lng": 80.2400},
    {"name": "Global Hospital & Health City", "lat": 12.9700, "lng": 80.2500},
]

FIRE_STATIONS = [
    {"name": "Chennai Fire Station Mylapore", "lat": 13.0340, "lng": 80.2640},
    {"name": "Chennai Fire Station Velachery", "lat": 12.9800, "lng": 80.2180},
]

POLICE_STATIONS = [
    {"name": "Chennai Police Mylapore", "lat": 13.0350, "lng": 80.2650},
    {"name": "Chennai Police Velachery", "lat": 12.9850, "lng": 80.2200},
]

NDRF_BASES = [
    {"name": "NDRF Base Chennai", "lat": 13.1900, "lng": 80.1200},
]

AMBULANCE_BASES = [
    {"name": "WIMS Ambulance Base 1", "lat": 13.0150, "lng": 80.2450},
    {"name": "Red Cross Ambulance Centre", "lat": 12.9900, "lng": 80.2300},
]

def call_osrm(start_lat, start_lng, end_lat, end_lng):
    """Call local OSRM for actual route."""
    try:
        url = f"http://localhost:5000/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            if data.get('routes') and len(data['routes']) > 0:
                route = data['routes'][0]
                coords = route['geometry']['coordinates']
                path_coords = [[c[1], c[0]] for c in coords]
                distance_km = round(route['distance'] / 1000, 2)
                return path_coords, distance_km
    except Exception as e:
        print(f"OSRM error: {e}", flush=True)
    return None, None

routes_data = {
    "hospitals": [],
    "fire_stations": [],
    "police_stations": [],
    "ndrf_bases": [],
    "ambulance_bases": []
}

print("Generating hospital routes...", flush=True)
for h in HOSPITALS:
    path, dist = call_osrm(h["lat"], h["lng"], INCIDENT_LAT, INCIDENT_LNG)
    if path:
        routes_data["hospitals"].append({
            "name": h["name"],
            "lat": h["lat"],
            "lng": h["lng"],
            "path_coords": path,
            "distance_km": dist,
            "type": "hospital"
        })
        print(f"  OK {h['name']}: {dist} km", flush=True)
    time.sleep(0.3)

print("Generating fire station routes...", flush=True)
for f in FIRE_STATIONS:
    path, dist = call_osrm(f["lat"], f["lng"], INCIDENT_LAT, INCIDENT_LNG)
    if path:
        routes_data["fire_stations"].append({
            "name": f["name"],
            "lat": f["lat"],
            "lng": f["lng"],
            "path_coords": path,
            "distance_km": dist,
            "type": "fire_station"
        })
        print(f"  ✓ {f['name']}: {dist} km", flush=True)
    time.sleep(0.3)

print("Generating police station routes...", flush=True)
for p in POLICE_STATIONS:
    path, dist = call_osrm(p["lat"], p["lng"], INCIDENT_LAT, INCIDENT_LNG)
    if path:
        routes_data["police_stations"].append({
            "name": p["name"],
            "lat": p["lat"],
            "lng": p["lng"],
            "path_coords": path,
            "distance_km": dist,
            "type": "police_station"
        })
        print(f"  ✓ {p['name']}: {dist} km", flush=True)
    time.sleep(0.3)

print("Generating NDRF routes...", flush=True)
for n in NDRF_BASES:
    path, dist = call_osrm(n["lat"], n["lng"], INCIDENT_LAT, INCIDENT_LNG)
    if path:
        routes_data["ndrf_bases"].append({
            "name": n["name"],
            "lat": n["lat"],
            "lng": n["lng"],
            "path_coords": path,
            "distance_km": dist,
            "type": "ndrf"
        })
        print(f"  ✓ {n['name']}: {dist} km", flush=True)
    time.sleep(0.3)

print("Generating ambulance routes...", flush=True)
for a in AMBULANCE_BASES:
    path, dist = call_osrm(a["lat"], a["lng"], INCIDENT_LAT, INCIDENT_LNG)
    if path:
        routes_data["ambulance_bases"].append({
            "name": a["name"],
            "lat": a["lat"],
            "lng": a["lng"],
            "path_coords": path,
            "distance_km": dist,
            "type": "ambulance"
        })
        print(f"  ✓ {a['name']}: {dist} km", flush=True)
    time.sleep(0.3)

print(json.dumps(routes_data, indent=2), flush=True)
