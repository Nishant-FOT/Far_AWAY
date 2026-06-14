"""
Unified database models for all agents.
Centralized incident tracking across the entire pipeline.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UnifiedIncidentRecord(Base):
    """
    Central incident record shared across all agents.
    Stores complete incident state as it flows through the pipeline.
    """
    __tablename__ = "unified_incidents"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Detection stage
    incident_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    incident_type: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[str] = mapped_column(String(200), index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    affected_population: Mapped[int] = mapped_column(Integer, default=0)
    casualties: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    water_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rainfall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Assessment stage
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    escalation_required: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    assessment_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Disaster agent outputs (stored as JSON)
    gis_output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    route_output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    communication_output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prediction_output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pipeline metadata
    pipeline_stage: Mapped[str] = mapped_column(
        String(50), default="detection", index=True
    )  # detection, assessment, gis, resource, route, communication, feedback, prediction
    creation_stage: Mapped[str] = mapped_column(
        String(50), default="detection"
    )  # Which agent created this record

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class IncidentPipelineLog(Base):
    """
    Log of incident state changes as it moves through the pipeline.
    For debugging and audit trail.
    """
    __tablename__ = "incident_pipeline_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[str] = mapped_column(String(100), index=True)
    stage: Mapped[str] = mapped_column(String(50), index=True)  # detection, assessment, gis, etc.
    action: Mapped[str] = mapped_column(String(200))  # What happened
    status: Mapped[str] = mapped_column(String(50))  # success, failed, skipped
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
