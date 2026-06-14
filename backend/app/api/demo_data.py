"""
HACKATHON DEMO MODE - Complete Precomputed Data
Incident: DEMO-CHENNAI-001 (Building Collapse - TVH Ouranya Bay)
Location: 12.812169, 80.230532
Routes: Real OSRM-based navigation
"""
import math
import os
from datetime import datetime, timedelta
import httpx


def _circle_polygon(center_lat, center_lon, km_radius, points=32):
    """Create approximate circular polygon in lat/lon."""
    coords = []
    for i in range(points):
        theta = 2 * math.pi * (i / points)
        dx = km_radius * math.cos(theta)
        dy = km_radius * math.sin(theta)
        dlat = dy / 111.0
        dlon = dx / (111.0 * math.cos(math.radians(center_lat)))
        coords.append([round(center_lon + dlon, 6), round(center_lat + dlat, 6)])
    coords.append(coords[0])
    return coords



# ============================================================================
# INCIDENT DATA
# ============================================================================

DEMO_INCIDENT_ID = "DEMO-CHENNAI-001"
DEMO_INCIDENT_LAT = 12.812169
DEMO_INCIDENT_LNG = 80.230532
DEMO_INCIDENT_NAME = "TVH Ouranya Bay"

def get_demo_incident():
    """DEMO-CHENNAI-001: Building Collapse"""
    now = datetime.utcnow().isoformat()
    return {
        "incident_id": DEMO_INCIDENT_ID,
        "incident_type": "Building Collapse",
        "severity": "Critical",
        "affected_population": 2500,
        "entrapped": 1500,
        "injured": 700,
        "fatalities": 300,
        "latitude": DEMO_INCIDENT_LAT,
        "longitude": DEMO_INCIDENT_LNG,
        "building": DEMO_INCIDENT_NAME,
        "floors": 30,
        "city": "Chennai",
        "timestamp": now,
        "description": "Multi-story building collapse in South Chennai. Critical rescue operation required."
    }


# ============================================================================
# GIS ZONES
# ============================================================================

def get_demo_gis():
    """GIS zones for building collapse: Critical (300m), Operational (700m), Safe (1500m)"""
    center_lat = DEMO_INCIDENT_LAT
    center_lon = DEMO_INCIDENT_LNG
    
    return {
        "incident_point": {
            "type": "Point",
            "coordinates": [center_lon, center_lat]
        },
        "critical_zone": {
            "type": "Polygon",
            "coordinates": [_circle_polygon(center_lat, center_lon, 0.3)]
        },
        "operational_zone": {
            "type": "Polygon",
            "coordinates": [_circle_polygon(center_lat, center_lon, 0.7)]
        },
        "safe_zone": {
            "type": "Polygon",
            "coordinates": [_circle_polygon(center_lat, center_lon, 1.5)]
        },
        "metadata": {
            "critical_radius_km": 0.3,
            "operational_radius_km": 0.7,
            "safe_radius_km": 1.5
        }
    }


def get_demo_zones():
    # Legacy compatibility
    gis = get_demo_gis()
    return {
        "critical_zone": gis["critical_zone"]["coordinates"][0],
        "operational_zone": gis["operational_zone"]["coordinates"][0],
        "safe_zone": gis["safe_zone"]["coordinates"][0],
        "affected_radius_km": 0.3,
    }


# ============================================================================
# RESOURCES & DEPLOYMENT
# ============================================================================

RESOURCE_LOCATIONS = {
    "hospitals": [
        {"name": "Apollo Speciality Hospital Nungambakkam", "lat": 13.0500, "lng": 80.2300, "id": "hosp_apollo"},
        {"name": "Sri Ramakrishna Hospital", "lat": 13.0200, "lng": 80.2400, "id": "hosp_sri"},
        {"name": "Global Hospital & Health City", "lat": 12.9700, "lng": 80.2500, "id": "hosp_global"},
    ],
    "fire_stations": [
        {"name": "Chennai Fire Station Mylapore", "lat": 13.0340, "lng": 80.2640, "id": "fire_mylapore"},
        {"name": "Chennai Fire Station Velachery", "lat": 12.9800, "lng": 80.2180, "id": "fire_velachery"},
    ],
    "police": [
        {"name": "Chennai Police Mylapore", "lat": 13.0350, "lng": 80.2650, "id": "police_mylapore"},
        {"name": "Chennai Police Velachery", "lat": 12.9850, "lng": 80.2200, "id": "police_velachery"},
    ],
    "ndrf": [
        {"name": "NDRF Base Chennai", "lat": 13.1900, "lng": 80.1200, "id": "ndrf_base"},
    ],
    "ambulance": [
        {"name": "WIMS Ambulance Base 1", "lat": 13.0150, "lng": 80.2450, "id": "ambulance_wims"},
        {"name": "Red Cross Ambulance Centre", "lat": 12.9900, "lng": 80.2300, "id": "ambulance_redcross"},
    ],
}


def get_demo_allocation():
    """Realistic resource allocation for building collapse rescue."""
    return {
        "ambulances": 30,
        "fire_tenders": 15,
        "rescue_teams": 10,
        "heavy_cranes": 5,
        "ndrf_teams": 2,
        "helicopters": 3,
        "medical_camps": 5,
        "food_supply_units": 4,
        "water_supply_units": 3,
        "total_personnel": 1850,
        "status": "Deployed"
    }


def get_demo_resources():
    """Return all resource locations deployed to incident."""
    resources = []
    for category, items in RESOURCE_LOCATIONS.items():
        for item in items:
            resources.append({
                "id": item.get("id", f"{category}_{len(resources)}"),
                "name": item["name"],
                "type": category.rstrip('s'),  # singular form
                "latitude": item["lat"],
                "longitude": item["lng"],
            })
    return resources


def _get_demo_routes_precomputed():
    """Routes precomputed via OSRM (fallback dummy routes)."""
    return {
        "hospitals": [
            {
                "id": "hosp_apollo",
                "name": "Apollo Speciality Hospital Nungambakkam",
                "lat": 13.0500,
                "lng": 80.2300,
                "type": "hospital",
                "distance_km": 25.8,
                "eta_minutes": 45,
                "path_coords": []
            },
            {
                "id": "hosp_sri",
                "name": "Sri Ramakrishna Hospital",
                "lat": 13.0200,
                "lng": 80.2400,
                "type": "hospital",
                "distance_km": 22.1,
                "eta_minutes": 38,
                "path_coords": []
            },
            {
                "id": "hosp_global",
                "name": "Global Hospital & Health City",
                "lat": 12.9700,
                "lng": 80.2500,
                "type": "hospital",
                "distance_km": 18.7,
                "eta_minutes": 32,
                "path_coords": []
            },
        ],
        "fire_stations": [
            {
                "id": "fire_mylapore",
                "name": "Chennai Fire Station Mylapore",
                "lat": 13.0340,
                "lng": 80.2640,
                "type": "fire_station",
                "distance_km": 26.2,
                "eta_minutes": 44,
                "path_coords": []
            },
            {
                "id": "fire_velachery",
                "name": "Chennai Fire Station Velachery",
                "lat": 12.9800,
                "lng": 80.2180,
                "type": "fire_station",
                "distance_km": 16.8,
                "eta_minutes": 28,
                "path_coords": []
            },
        ],
        "police_stations": [
            {
                "id": "police_mylapore",
                "name": "Chennai Police Mylapore",
                "lat": 13.0350,
                "lng": 80.2650,
                "type": "police",
                "distance_km": 26.5,
                "eta_minutes": 44,
                "path_coords": []
            },
            {
                "id": "police_velachery",
                "name": "Chennai Police Velachery",
                "lat": 12.9850,
                "lng": 80.2200,
                "type": "police",
                "distance_km": 17.1,
                "eta_minutes": 28,
                "path_coords": []
            },
        ],
        "ndrf_bases": [
            {
                "id": "ndrf_base",
                "name": "NDRF Base Chennai",
                "lat": 13.1900,
                "lng": 80.1200,
                "type": "ndrf",
                "distance_km": 32.4,
                "eta_minutes": 52,
                "path_coords": []
            },
        ],
        "ambulance_bases": [
            {
                "id": "ambulance_wims",
                "name": "WIMS Ambulance Base 1",
                "lat": 13.0150,
                "lng": 80.2450,
                "type": "ambulance",
                "distance_km": 19.3,
                "eta_minutes": 32,
                "path_coords": []
            },
            {
                "id": "ambulance_redcross",
                "name": "Red Cross Ambulance Centre",
                "lat": 12.9900,
                "lng": 80.2300,
                "type": "ambulance",
                "distance_km": 14.2,
                "eta_minutes": 24,
                "path_coords": []
            },
        ]
    }


def get_demo_routes_display():
    """Route data formatted for frontend display."""
    return _get_demo_routes_precomputed()


def _line(a_lat, a_lon, b_lat, b_lon, steps=10):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append([round(a_lat + (b_lat - a_lat) * t, 6), round(a_lon + (b_lon - a_lon) * t, 6)])
    return pts


def get_demo_routes():
    resources = get_demo_resources()
    center = (DEMO_CENTER["latitude"], DEMO_CENTER["longitude"])
    routes = []
    for r in resources:
        lat = r["location"]["latitude"]
        lon = r["location"]["longitude"]
        path = _line(lat, lon, center[0], center[1], steps=8)
        routes.append({
            "resource_id": r["id"],
            "resource_type": r["type"],
            "path_coords": path,
            "distance_km": round(0.5 + abs(lat - center[0]) * 111 + abs(lon - center[1]) * 111, 3),
        })
    # evacuation escape path
    escape = {"path_coords": _line(center[0], center[1], center[0]+0.05, center[1]+0.05, steps=12), "type": "escape", "distance_km": 7.1}
    return {"routes": routes, "escape": escape}


# ============================================================================
# PREDICTION
# ============================================================================

def get_demo_prediction():
    """Precomputed disaster prediction."""
    return {
        "rescue_duration_hours": 72,
        "infrastructure_damage_percent": 95,
        "rescue_success_probability": 0.88,
        "critical_casualties": 700,
        "recovery_time_days": 14,
        "economic_impact_crores": 2850,
        "structural_instability_score": 9.2,
        "secondary_hazards": [
            "Gas leaks in basement levels",
            "Electrical hazards from downed lines",
            "Unstable debris causing landslides on adjacent structures"
        ]
    }


# ============================================================================
# LEARNING / HISTORICAL
# ============================================================================

def get_demo_learning():
    """Lessons from similar incidents."""
    return {
        "similar_incidents": [
            {
                "year": 2013,
                "event": "East Coast Accident",
                "location": "Kolkata",
                "casualties": 1040,
                "lessons": [
                    "Immediate heavy machinery deployment critical",
                    "Coordinate with local NGOs for rapid response",
                    "Establish safe corridors for evacuation",
                    "Deploy medical triage before evacuation"
                ]
            },
            {
                "year": 2010,
                "event": "Hotel Collapse",
                "location": "Mumbai",
                "casualties": 54,
                "lessons": [
                    "First 72 hours are critical for rescue",
                    "Require specialized structural engineers immediately",
                    "Heavy rescue equipment must be pre-positioned"
                ]
            }
        ],
        "best_practices": [
            "Rapid situational assessment within first hour",
            "Establish incident command post immediately",
            "Pre-position medical teams at scene",
            "Coordinate with state disaster management",
            "Continuous structural safety assessment"
        ],
        "recommendations": [
            "Deploy NDRF teams within 4 hours",
            "Set up medical camps 500m from incident",
            "Establish evacuation corridors",
            "Monitor for aftershocks and secondary collapses",
            "Engage structural engineers for stabilization"
        ]
    }


# ============================================================================
# TIMELINE
# ============================================================================

def get_demo_timeline():
    """Incident response timeline."""
    base_time = datetime.utcnow()
    return [
        {"stage": 1, "timestamp": (base_time).isoformat(), "event": "Building Collapse Detected", "status": "completed"},
        {"stage": 2, "timestamp": (base_time + timedelta(minutes=5)).isoformat(), "event": "Initial Assessment", "status": "completed"},
        {"stage": 3, "timestamp": (base_time + timedelta(minutes=15)).isoformat(), "event": "Resource Allocation", "status": "completed"},
        {"stage": 4, "timestamp": (base_time + timedelta(minutes=30)).isoformat(), "event": "First Responders Dispatch", "status": "in-progress"},
        {"stage": 5, "timestamp": (base_time + timedelta(hours=1, minutes=30)).isoformat(), "event": "Rescue Teams Arrival", "status": "in-progress"},
        {"stage": 6, "timestamp": (base_time + timedelta(hours=4)).isoformat(), "event": "Medical Evacuation Begins", "status": "pending"},
        {"stage": 7, "timestamp": (base_time + timedelta(hours=24)).isoformat(), "event": "Structural Stabilization", "status": "pending"},
        {"stage": 8, "timestamp": (base_time + timedelta(days=3)).isoformat(), "event": "Search & Rescue Complete", "status": "pending"},
        {"stage": 9, "timestamp": (base_time + timedelta(days=14)).isoformat(), "event": "Recovery Phase", "status": "pending"},
    ]


# ============================================================================
# DEMO REPLAY (Unified Response)
# ============================================================================

def get_demo_replay():
    """Complete demo replay with all stages."""
    incident = get_demo_incident()
    
    stages = [
        {
            "stage": "detection",
            "kind": "incident_detected",
            "output": incident,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "stage": "assessment",
            "kind": "initial_assessment",
            "output": {
                "severity": "Critical",
                "affected_population": 2500,
                "entrapped": 1500
            },
            "timestamp": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        },
        {
            "stage": "gis",
            "kind": "zones_delineated",
            "extras": {
                "zones": get_demo_gis()
            },
            "timestamp": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        },
        {
            "stage": "resource",
            "kind": "resources_identified",
            "extras": {
                "allocation": get_demo_allocation(),
                "locations": get_demo_resources()
            },
            "timestamp": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        },
        {
            "stage": "route",
            "kind": "routes_optimized",
            "extras": {
                "routes": get_demo_routes_display()
            },
            "timestamp": (datetime.utcnow() + timedelta(minutes=20)).isoformat()
        },
        {
            "stage": "prediction",
            "kind": "impact_predicted",
            "extras": {
                "prediction": get_demo_prediction()
            },
            "timestamp": (datetime.utcnow() + timedelta(minutes=25)).isoformat()
        },
        {
            "stage": "learning",
            "kind": "lessons_retrieved",
            "extras": {
                "learning": get_demo_learning()
            },
            "timestamp": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        },
        {
            "stage": "final",
            "kind": "incident_complete",
            "output": {
                "incident": incident,
                "gis": get_demo_gis(),
                "resources": get_demo_resources(),
                "allocation": get_demo_allocation(),
                "routes": get_demo_routes_display(),
                "prediction": get_demo_prediction(),
                "learning": get_demo_learning(),
                "timeline": get_demo_timeline()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    return {
        "incident_id": DEMO_INCIDENT_ID,
        "stages": stages,
        "completed_at": datetime.utcnow().isoformat()
    }


def get_demo_dashboard():
    """Dashboard summary for demo."""
    return {
        "active_incident": get_demo_incident(),
        "affected_population": 2500,
        "resources_deployed": len(get_demo_resources()),
        "prediction": get_demo_prediction(),
        "allocation": get_demo_allocation(),
        "timeline": get_demo_timeline()
    }


# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

def _line(a_lat, a_lon, b_lat, b_lon, steps=10):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append([round(a_lat + (b_lat - a_lat) * t, 6), round(a_lon + (b_lon - a_lon) * t, 6)])
    return pts


def get_demo_simulation(steps=12):
    """Legacy simulation endpoint."""
    base_r = get_demo_zones().get("affected_radius_km", 0.3)
    timeseries = []
    for i in range(steps):
        factor = 1.0 + (i * 0.1)
        timeseries.append({"t": i, "radius_km": round(base_r * factor, 3), "center": {"latitude": DEMO_INCIDENT_LAT, "longitude": DEMO_INCIDENT_LNG}})
    return {"incident_id": DEMO_INCIDENT_ID, "timeseries": timeseries}
            "distance_km": distance_km,
        })
    return {"routes": routes}


def get_collapse_prediction():
    return {
        "escalation_probability": 0.12,
        "predicted_population_impact": 30,
        "infrastructure_impact": "Localized",
        "recovery_time_days": 2,
    }


def get_collapse_learning():
    return {"similar_events": [{"year": 2019, "event": "Local building collapse", "lessons": ["Rapid medical response", "Heavy-lifting equipment"]}], "insights": ["Targeted urban search and rescue required"]}


def get_collapse_timeline():
    return [{"minute": 0, "event": "Collapse reported"}, {"minute": 10, "event": "First responders dispatched"}, {"minute": 30, "event": "Victims triaged"}]


def get_collapse_dashboard():
    resources = get_collapse_resources()
    deployed = [r for r in resources if r["type"] in ("fire_station", "hospital")]
    return {"active_incident": get_collapse_incident(), "affected_population": 25, "resources_deployed": len(deployed), "prediction": get_collapse_prediction(), "evacuation_progress": 0.0, "shelter_occupancy": {"capacity_total": 200, "occupied": 12}}


def get_collapse_replay():
    state = get_collapse_incident()
    state.update({
        "gis_output": get_collapse_gis(),
        "resources": get_collapse_resources(),
        "routes": get_collapse_routes(),
        "prediction": get_collapse_prediction(),
        "learning": get_collapse_learning(),
        "timeline": get_collapse_timeline(),
        "dashboard": get_collapse_dashboard(),
    })
    stages = [
        {"stage": "assessment", "output": {"severity": state["severity"]}},
        {"stage": "resource", "output": get_collapse_resources()},
        {"stage": "route", "output": get_collapse_routes()},
        {"stage": "final", "output": state},
    ]
    return {"incident_id": state["incident_id"], "stages": stages}

