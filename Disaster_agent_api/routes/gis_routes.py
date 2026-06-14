"""
GIS Agent API wrapper.
Exposes the existing GIS agent as a REST endpoint.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
import re
from geopy.distance import geodesic
import math

# Import the existing GIS agent
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../Disaster'))

from agents.gis_agent import SimplifiedBayesianRiskAssessor

router = APIRouter(prefix="/api/v1/gis", tags=["gis"])

# Singleton instance
_gis_agent = SimplifiedBayesianRiskAssessor()


# ─────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────


class GISAnalysisRequest(BaseModel):
    """Request for GIS risk analysis."""
    incident_id: str
    incident_type: str
    affected_population: int
    latitude: float
    longitude: float
    hazard_severity: str  # High, Medium, Low
    population_density: str  # High, Medium, Low
    infrastructure_vulnerability: str  # High, Medium, Low
    resource_availability: Optional[str] = "Medium"  # High, Medium, Low
    environmental_condition: Optional[str] = "Medium"  # High, Medium, Low


class NearbyResource(BaseModel):
    """Nearby resource location."""
    name: str
    latitude: float
    longitude: float
    distance_km: float


class GISAnalysisResponse(BaseModel):
    """Response from GIS analysis."""
    incident_id: str
    hazard_severity: str
    population_density: str
    infrastructure_vulnerability: str
    risk_probability: float
    affected_radius_km: float
    nearby_resources: List[NearbyResource]
    environmental_condition: str
    resource_availability: str
    map_html_path: Optional[str] = None
    timestamp: datetime = None


# ─────────────────────────────────────────────────────────────────────
# GIS Endpoints
# ─────────────────────────────────────────────────────────────────────


@router.post("/analyze")
async def gis_analyze(request: GISAnalysisRequest) -> GISAnalysisResponse:
    """
    Analyze disaster risk using GIS agent.
    Computes risk probability, affected radius, and nearby resources.
    """
    try:
        # Call existing GIS agent infer method
        result = _gis_agent.infer(
            hazard_severity=request.hazard_severity,
            population_density=request.population_density,
            infrastructure_vulnerability=request.infrastructure_vulnerability,
            resource_availability=request.resource_availability,
            environmental_condition=request.environmental_condition,
            disaster_type=request.incident_type,
        )

        # Extract risk probability from result
        risk_prob = result.get("probability", 0.5)

        # Compute affected radius based on risk
        affected_radius = 5.0 * (1.0 + risk_prob)  # Scale radius by risk

        return GISAnalysisResponse(
            incident_id=request.incident_id,
            hazard_severity=request.hazard_severity,
            population_density=request.population_density,
            infrastructure_vulnerability=request.infrastructure_vulnerability,
            risk_probability=risk_prob,
            affected_radius_km=affected_radius,
            nearby_resources=[],
            environmental_condition=request.environmental_condition,
            resource_availability=request.resource_availability,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GIS analysis failed: {str(e)}")


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "gis_agent"}


@router.get("/resources")
async def list_resources():
    """Return resource locations from Disaster/data/resources.json (node_key added)."""
    try:
        resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Disaster/data/resources.json'))
        if not os.path.exists(resources_path):
            raise HTTPException(status_code=404, detail="Resources file not found")

        with open(resources_path, encoding='utf-8') as f:
            data = json.load(f)

        def node_key(name: str) -> str:
            key = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            return key

        for r in data:
            r['node_key'] = node_key(r.get('name', ''))

        return {"resources": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load resources: {str(e)}")


# ------------------------------------------------------------------
# Zone generation endpoint (GeoJSON circles)
# ------------------------------------------------------------------


class ZoneRequest(BaseModel):
    incident_id: str
    incident_type: str
    latitude: float
    longitude: float
    hazard_severity: str
    population_density: Optional[str] = "Medium"
    infrastructure_vulnerability: Optional[str] = "Medium"


def _circle_polygon(lat: float, lon: float, radius_km: float, points: int = 64):
    """Approximate a circle as a GeoJSON polygon using geodesic destinations."""
    coords = []
    for i in range(points + 1):
        bearing = float(i) * (360.0 / points)
        dest = geodesic(kilometers=radius_km).destination((lat, lon), bearing)
        coords.append([round(dest.longitude, 6), round(dest.latitude, 6)])
    return coords


@router.post("/zones")
async def generate_zones(req: ZoneRequest):
    """Generate concentric zones (critical/moderate/safe) as GeoJSON polygons."""
    try:
        # Use the existing simplified risk assessor for probability
        result = _gis_agent.infer(
            hazard_severity=req.hazard_severity,
            population_density=req.population_density,
            infrastructure_vulnerability=req.infrastructure_vulnerability,
            disaster_type=req.incident_type,
        )

        risk_prob = result.get("probability", 0.5)
        # Base affected radius (km) — keep same heuristic as analyze()
        base_radius = 5.0 * (1.0 + risk_prob)

        # Generate concentric radii
        critical_r = round(base_radius * 0.5, 3)
        moderate_r = round(base_radius * 0.85, 3)
        safe_r = round(base_radius * 1.25, 3)

        zones = {
            "critical": {
                "type": "Feature",
                "properties": {"level": "CRITICAL", "radius_km": critical_r, "color": "red"},
                "geometry": {"type": "Polygon", "coordinates": [_circle_polygon(req.latitude, req.longitude, critical_r)]},
            },
            "moderate": {
                "type": "Feature",
                "properties": {"level": "MODERATE", "radius_km": moderate_r, "color": "orange"},
                "geometry": {"type": "Polygon", "coordinates": [_circle_polygon(req.latitude, req.longitude, moderate_r)]},
            },
            "safe": {
                "type": "Feature",
                "properties": {"level": "SAFE", "radius_km": safe_r, "color": "green"},
                "geometry": {"type": "Polygon", "coordinates": [_circle_polygon(req.latitude, req.longitude, safe_r)]},
            },
        }

        return {
            "incident_id": req.incident_id,
            "risk_probability": risk_prob,
            "affected_radius_km": base_radius,
            "zones_geojson": {"type": "FeatureCollection", "features": [zones["critical"], zones["moderate"], zones["safe"]]},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zone generation failed: {str(e)}")
