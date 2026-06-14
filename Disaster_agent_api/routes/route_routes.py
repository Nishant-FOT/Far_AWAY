"""
Route Agent API wrapper.
Exposes the existing Route agent as a REST endpoint.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import the existing Route agent
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../Disaster'))

from agents.route_agent import RouteOptimizationAgent

router = APIRouter(prefix="/api/v1/route", tags=["route"])

# Singleton instance
_route_agent = RouteOptimizationAgent()


# ─────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────


class RouteSegmentResponse(BaseModel):
    """Single segment in a route."""
    from_node: str
    to_node: str
    distance_km: float
    time_minutes: float
    flood_risk: float
    road_damage: float


class ResourceRouteResponse(BaseModel):
    """Route from a resource to incident location."""
    resource_location: str
    resource_type: str
    incident_location: str
    total_distance_km: float
    total_time_minutes: float
    segments: List[RouteSegmentResponse]
    blocked_roads: List[str]
    path: List[str] = []
    path_coords: List[List[float]] = []


class RouteOptimizationRequest(BaseModel):
    """Request for route optimization."""
    incident_id: str
    incident_location: str
    incident_lat: Optional[float] = None
    incident_lon: Optional[float] = None
    available_resources: List[str]  # Resource locations


class RouteOptimizationResponse(BaseModel):
    """Response from route optimization."""
    incident_id: str
    incident_location: str
    incident_lat: Optional[float] = None
    incident_lon: Optional[float] = None
    routes: List[ResourceRouteResponse]
    fastest_route: Optional[ResourceRouteResponse] = None
    recommendations: List[str]
    timestamp: datetime = None


# ─────────────────────────────────────────────────────────────────────
# Route Endpoints
# ─────────────────────────────────────────────────────────────────────


@router.post("/optimize")
async def optimize_routes(request: RouteOptimizationRequest) -> RouteOptimizationResponse:
    """
    Find optimal routes from resources to incident location.
    Uses A* algorithm with dynamic road risk weights.
    """
    try:
        routes = []
        fastest_route = None
        fastest_time = float("inf")

        # Resolve incident node: prefer explicit incident_location, otherwise snap from lat/lon
        incident_node = request.incident_location
        if (not incident_node or incident_node.strip() == "") and request.incident_lat is not None and request.incident_lon is not None:
            incident_node = _route_agent.nearest_node(request.incident_lat, request.incident_lon)

        if not incident_node:
            raise HTTPException(status_code=400, detail="No valid incident location provided")

        for resource_loc in request.available_resources:
            try:
                route_result = _route_agent.find_route(resource_loc, incident_node)

                if route_result and isinstance(route_result, dict) and route_result.get('status') == 'OK':
                    segments = []
                    total_distance = route_result.get('distance_km', 0.0)
                    total_time = route_result.get('time_minutes', 0.0)
                    path = route_result.get('path', [])

                    # Convert path node names to coordinates
                    path_coords = []
                    for node_name in path:
                        coords = _route_agent.node_coords(node_name)
                        if coords:
                            lat, lon = coords
                            path_coords.append([lat, lon])

                    route_response = ResourceRouteResponse(
                        resource_location=resource_loc,
                        resource_type="unknown",
                        incident_location=incident_node,
                        total_distance_km=total_distance,
                        total_time_minutes=total_time,
                        segments=segments,
                        blocked_roads=route_result.get('blocked_roads_active', []),
                        path=path,
                        path_coords=path_coords,
                    )
                    routes.append(route_response)

                    # Track fastest route
                    if total_time < fastest_time:
                        fastest_time = total_time
                        fastest_route = route_response
            except Exception:
                # Skip this resource if route fails
                continue

        recommendations = []
        if fastest_route:
            recommendations.append(
                f"Use route from {fastest_route.resource_location} "
                f"({fastest_route.total_time_minutes:.1f} min)"
            )

        return RouteOptimizationResponse(
            incident_id=request.incident_id,
            incident_location=request.incident_location,
            incident_lat=request.incident_lat,
            incident_lon=request.incident_lon,
            routes=routes,
            fastest_route=fastest_route,
            recommendations=recommendations,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "route_agent"}
