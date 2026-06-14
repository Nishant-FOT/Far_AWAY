"""
Unified incident schemas used across all agents.
Backwards compatible with existing Detection and Assessment schemas.
"""

from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────
# Input Schemas
# ─────────────────────────────────────────────────────────────────────


class UnifiedIncidentInput(BaseModel):
    """
    Unified incident input that can be created by Detection agent
    and consumed by Assessment, GIS, Resource, Route, Communication agents.
    """
    incident_id: Optional[str] = None
    incident_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    affected_population: int = 0
    casualties: int = 0
    confidence: float
    urgency: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_count: int = 1
    water_level: Optional[float] = None
    rainfall: Optional[float] = None
    temperature: Optional[float] = None
    timestamp: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────
# GIS Agent Output Schema
# ─────────────────────────────────────────────────────────────────────


class GISRiskOutput(BaseModel):
    """Output from GIS Agent risk analysis."""
    incident_id: str
    hazard_severity: str  # High, Medium, Low
    population_density: str  # High, Medium, Low
    infrastructure_vulnerability: str  # High, Medium, Low
    risk_probability: float = Field(ge=0.0, le=1.0)  # 0-1 scale
    affected_radius_km: float  # Kilometers
    nearby_resources: List[dict] = Field(default_factory=list)  # [{name, lat, lon, distance_km}, ...]
    map_html_path: Optional[str] = None
    environmental_condition: Optional[str] = None  # High, Medium, Low
    resource_availability: Optional[str] = None  # High, Medium, Low


# ─────────────────────────────────────────────────────────────────────
# Resource Agent Output Schema
# ─────────────────────────────────────────────────────────────────────


class ResourceAllocationOutput(BaseModel):
    """Output from Resource Agent allocation."""
    incident_id: str
    priority_score: float = Field(ge=0.0, le=100.0)
    required_resources: dict  # {resource_type: count}
    deployment_order: List[str] = Field(default_factory=list)
    availability_status: str  # Adequate, Moderate, Critical
    shortage_areas: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# Route Agent Output Schema
# ─────────────────────────────────────────────────────────────────────


class RouteSegment(BaseModel):
    """Single segment in a route."""
    from_node: str
    to_node: str
    distance_km: float
    time_minutes: float
    flood_risk: float = Field(ge=0.0, le=1.0)
    road_damage: float = Field(ge=0.0, le=1.0)


class ResourceRoute(BaseModel):
    """Route from a resource to incident location."""
    resource_location: str
    resource_type: str
    incident_location: str
    total_distance_km: float
    total_time_minutes: float
    segments: List[RouteSegment] = Field(default_factory=list)
    blocked_roads: List[str] = Field(default_factory=list)


class RouteOptimizationOutput(BaseModel):
    """Output from Route Agent."""
    incident_id: str
    incident_location: str
    incident_lat: Optional[float] = None
    incident_lon: Optional[float] = None
    routes: List[ResourceRoute] = Field(default_factory=list)
    fastest_route: Optional[ResourceRoute] = None
    recommendations: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# Communication Agent Output Schema
# ─────────────────────────────────────────────────────────────────────


class Alert(BaseModel):
    """Single alert message."""
    target_audience: str  # citizen, authority, sms
    language: str  # en, hi
    severity: str  # advisory, warning, evacuation
    message: str
    action_recommended: Optional[str] = None


class CommunicationOutput(BaseModel):
    """Output from Communication Agent."""
    incident_id: str
    alerts: List[Alert] = Field(default_factory=list)
    broadcast_ready: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────
# Feedback Agent Output Schema
# ─────────────────────────────────────────────────────────────────────


class FeedbackEntry(BaseModel):
    """Single feedback report."""
    feedback_id: str
    incident_id: str
    feedback_type: str
    source_type: str
    trust_score: float = Field(ge=0.0, le=1.0)
    message: str
    timestamp: datetime


class FeedbackAction(BaseModel):
    """Recommended action from feedback analysis."""
    action_type: str  # BLOCK_ROAD, UNBLOCK_ROAD, INCREASE_RESOURCES, etc.
    target: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class FeedbackOutput(BaseModel):
    """Output from Feedback Agent."""
    incident_id: str
    total_feedback_count: int
    corroborated: bool
    average_trust_score: float
    recommended_actions: List[FeedbackAction] = Field(default_factory=list)
    statistics: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────
# Prediction Agent Output Schema
# ─────────────────────────────────────────────────────────────────────


class PredictionOutput(BaseModel):
    """Output from Prediction Agent."""
    incident_id: str
    escalation_probability: float = Field(ge=0.0, le=1.0)
    predicted_severity: str  # High, Medium, Low
    population_impact: int  # Estimated total affected
    infrastructure_impact: float = Field(ge=0.0, le=1.0)  # Proportion of infrastructure at risk
    resource_forecast: dict  # {resource_type: recommended_count}
    recommended_actions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────
# Unified Incident State (Full Pipeline Result)
# ─────────────────────────────────────────────────────────────────────


class IncidentState(BaseModel):
    """
    Complete incident state as it flows through the pipeline.
    Updated at each stage by the respective agents.
    """
    # Detection stage
    incident_id: str
    incident_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    affected_population: int = 0
    casualties: int = 0
    confidence: float
    urgency: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_count: int = 1
    water_level: Optional[float] = None
    rainfall: Optional[float] = None
    temperature: Optional[float] = None

    # Assessment stage
    severity: Optional[str] = None
    priority: Optional[str] = None
    risk_score: Optional[int] = None
    resource_urgency: Optional[str] = None
    escalation_required: Optional[bool] = None
    assessment_explanation: Optional[str] = None

    # Disaster agent outputs
    gis_output: Optional[GISRiskOutput] = None
    resource_output: Optional[ResourceAllocationOutput] = None
    route_output: Optional[RouteOptimizationOutput] = None
    communication_output: Optional[CommunicationOutput] = None
    feedback_output: Optional[FeedbackOutput] = None
    prediction_output: Optional[PredictionOutput] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_stage: str = "detection"  # detection, assessment, gis, resource, route, communication, feedback, prediction
