"""
Resource Agent API wrapper.
Exposes the existing Resource agent as a REST endpoint.
"""

from datetime import datetime
from typing import Optional, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import the existing Resource agent
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../Disaster'))

from agents.resource_agent import ResourceAllocationAgent

router = APIRouter(prefix="/api/v1/resource", tags=["resource"])

# Singleton instance
_resource_agent = ResourceAllocationAgent()


# ─────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────


class ResourceAllocationRequest(BaseModel):
    """Request for resource allocation."""
    incident_id: str
    incident_type: str
    risk_probability: float  # 0-1
    affected_population: int
    infrastructure_vulnerability: str  # High, Medium, Low
    resource_availability: str  # High, Medium, Low


class ResourceDeploymentPlan(BaseModel):
    """Resource deployment plan."""
    incident_id: str
    priority_score: float
    required_resources: Dict[str, int]
    deployment_order: List[str]
    availability_status: str
    shortage_areas: List[str]
    timestamp: datetime = None


# ─────────────────────────────────────────────────────────────────────
# Resource Endpoints
# ─────────────────────────────────────────────────────────────────────


@router.post("/allocate")
async def allocate_resources(request: ResourceAllocationRequest) -> ResourceDeploymentPlan:
    """
    Allocate resources for the disaster using resource agent.
    Returns deployment plan and resource requirements.
    """
    try:
        # Infer severity from risk probability
        severity = "High" if request.risk_probability > 0.7 else "Medium" if request.risk_probability > 0.4 else "Low"
        
        # Infer population density
        if request.affected_population > 10000:
            population_density = "High"
        elif request.affected_population > 1000:
            population_density = "Medium"
        else:
            population_density = "Low"

        # Call existing Resource agent allocate method
        result = _resource_agent.allocate(
            incident_type=request.incident_type,
            severity=severity,
            risk_probability=request.risk_probability,
            population_density=population_density,
            resource_availability=request.resource_availability,
            infrastructure_vulnerability=request.infrastructure_vulnerability,
            affected_population=request.affected_population,
            deduct_from_inventory=False,  # Don't actually deduct from shared inventory
        )

        # Extract results
        required_resources = result.get("resources", {})
        deployment_order = result.get("deployment_order", [])
        priority_score = result.get("priority_score", 0.0)
        shortage_areas = list(result.get("shortfall", {}).keys()) if result.get("shortfall") else []

        # Availability status
        if request.resource_availability == "High":
            availability_status = "Adequate"
        elif request.resource_availability == "Medium":
            availability_status = "Moderate"
        else:
            availability_status = "Critical"

        return ResourceDeploymentPlan(
            incident_id=request.incident_id,
            priority_score=priority_score,
            required_resources=required_resources,
            deployment_order=deployment_order,
            availability_status=availability_status,
            shortage_areas=shortage_areas,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resource allocation failed: {str(e)}")


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "resource_agent"}
