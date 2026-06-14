"""
Integration tests for the full Disaster Management Pipeline.
Tests the flow: Detection → Assessment → GIS → Resource → Route → Communication → Feedback → Prediction
"""

import pytest
import asyncio
from datetime import datetime

# These tests would require running all services, so they're more like smoke tests
# For now, we'll test the individual components

def test_unified_schemas_import():
    """Test that unified schemas can be imported."""
    from shared.schemas import (
        UnifiedIncidentInput,
        IncidentState,
        GISRiskOutput,
        ResourceAllocationOutput,
        RouteOptimizationOutput,
        CommunicationOutput,
        FeedbackOutput,
        PredictionOutput,
    )
    assert UnifiedIncidentInput is not None
    assert IncidentState is not None


def test_database_models_import():
    """Test that database models can be imported."""
    from shared.database_models import UnifiedIncidentRecord, IncidentPipelineLog
    assert UnifiedIncidentRecord is not None
    assert IncidentPipelineLog is not None


def test_prediction_engine_import():
    """Test that Prediction Engine can be imported."""
    from Prediction_agent.prediction_engine import PredictionEngine, PredictionRequest, PredictionResponse
    assert PredictionEngine is not None
    assert PredictionRequest is not None
    assert PredictionResponse is not None


def test_prediction_engine_basic():
    """Test basic prediction engine functionality."""
    from Prediction_agent.prediction_engine import (
        PredictionEngine,
        PredictionRequest,
        DetectionData,
        AssessmentData,
        GISData,
        ResourceData,
    )

    engine = PredictionEngine()

    # Create a test request
    request = PredictionRequest(
        incident_id="INC-001",
        incident_type="Flood",
        detection_output=DetectionData(
            confidence=0.85,
            affected_population=5000,
            casualties=10,
        ),
        assessment_output=AssessmentData(
            severity="High",
            risk_score=85,
        ),
        gis_output=GISData(
            risk_probability=0.8,
            affected_radius_km=5.0,
            infrastructure_vulnerability="Medium",
            resource_availability="Medium",
        ),
        resource_output=ResourceData(
            priority_score=75.0,
            availability_status="Moderate",
        ),
    )

    # Make prediction
    response = engine.predict(request)

    # Validate response
    assert response.incident_id == "INC-001"
    assert 0.0 <= response.escalation_probability <= 1.0
    assert response.predicted_severity in ["High", "Medium", "Low"]
    assert response.population_impact > 0
    assert 0.0 <= response.infrastructure_impact <= 1.0
    assert len(response.resource_forecast) > 0
    assert len(response.recommended_actions) > 0
    assert 0.0 <= response.confidence <= 1.0


def test_prediction_high_escalation():
    """Test prediction with high escalation risk."""
    from Prediction_agent.prediction_engine import (
        PredictionEngine,
        PredictionRequest,
        DetectionData,
        AssessmentData,
        GISData,
        ResourceData,
    )

    engine = PredictionEngine()

    # High-risk scenario
    request = PredictionRequest(
        incident_id="INC-002",
        incident_type="Cyclone",
        detection_output=DetectionData(
            confidence=0.95,
            affected_population=50000,
            casualties=100,
        ),
        assessment_output=AssessmentData(
            severity="High",
            risk_score=95,
        ),
        gis_output=GISData(
            risk_probability=0.95,
            affected_radius_km=20.0,
            infrastructure_vulnerability="High",
            resource_availability="Low",
        ),
    )

    response = engine.predict(request)

    # High escalation risk expected
    assert response.escalation_probability > 0.7
    assert response.predicted_severity == "High"
    assert response.population_impact > 50000


def test_prediction_low_escalation():
    """Test prediction with low escalation risk."""
    from Prediction_agent.prediction_engine import (
        PredictionEngine,
        PredictionRequest,
        DetectionData,
        AssessmentData,
        GISData,
        ResourceData,
    )

    engine = PredictionEngine()

    # Low-risk scenario
    request = PredictionRequest(
        incident_id="INC-003",
        incident_type="Landslide",
        detection_output=DetectionData(
            confidence=0.5,
            affected_population=200,
            casualties=0,
        ),
        assessment_output=AssessmentData(
            severity="Low",
            risk_score=25,
        ),
        gis_output=GISData(
            risk_probability=0.2,
            affected_radius_km=1.0,
            infrastructure_vulnerability="Low",
            resource_availability="High",
        ),
    )

    response = engine.predict(request)

    # Low escalation risk expected
    assert response.escalation_probability < 0.4
    assert response.predicted_severity in ["Low", "Medium"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
