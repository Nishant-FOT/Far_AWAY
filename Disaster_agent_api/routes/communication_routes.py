"""
Communication Agent API wrapper.
Exposes the existing Communication agent as a REST endpoint.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import the existing Communication agent
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../Disaster'))

from agents.communication_agent import CommunicationAgent

router = APIRouter(prefix="/api/v1/communication", tags=["communication"])

# Singleton instance
_comm_agent = CommunicationAgent()


# ─────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────


class AlertMessage(BaseModel):
    """Single alert message."""
    target_audience: str  # citizen, authority, sms
    language: str  # en, hi
    severity: str  # advisory, warning, evacuation
    message: str
    action_recommended: Optional[str] = None


class CommunicationRequest(BaseModel):
    """Request for communication generation."""
    incident_id: str
    incident_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    affected_population: int
    severity: str  # High, Medium, Low
    risk_score: Optional[float] = None


class CommunicationResponse(BaseModel):
    """Response with generated alerts."""
    incident_id: str
    alerts: List[AlertMessage]
    broadcast_ready: bool = False
    timestamp: datetime = None


# ─────────────────────────────────────────────────────────────────────
# Communication Endpoints
# ─────────────────────────────────────────────────────────────────────


@router.post("/generate-alerts")
async def generate_alerts(request: CommunicationRequest) -> CommunicationResponse:
    """
    Generate emergency alerts for citizens, authorities, and SMS broadcast.
    Uses template-based generation or LLM-enhanced if configured.
    """
    try:
        # Build incident dict for communication agent
        incident = {
            "incident_id": request.incident_id,
            "incident_type": request.incident_type,
            "location": request.location,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "affected_population": request.affected_population,
        }

        # Build risk dict
        risk = {
            "severity": request.severity,
            "risk_score": request.risk_score or 0.0,
        }

        # Generate all alerts using existing agent
        alerts_dict = _comm_agent.generate_all(
            incident=incident,
            risk=risk,
            allocation=None,
            route=None,
        )

        # Convert to response format
        alerts = []
        if "citizen" in alerts_dict:
            alerts.append(
                AlertMessage(
                    target_audience="citizen",
                    language="en",
                    severity=request.severity.lower(),
                    message=alerts_dict["citizen"].get("en", ""),
                    action_recommended="Evacuate immediately" if request.severity == "High" else None,
                )
            )
            if "hi" in alerts_dict["citizen"]:
                alerts.append(
                    AlertMessage(
                        target_audience="citizen",
                        language="hi",
                        severity=request.severity.lower(),
                        message=alerts_dict["citizen"]["hi"],
                        action_recommended="तुरंत निकालें" if request.severity == "High" else None,
                    )
                )

        if "authority" in alerts_dict:
            alerts.append(
                AlertMessage(
                    target_audience="authority",
                    language="en",
                    severity=request.severity.lower(),
                    message=alerts_dict["authority"],
                )
            )

        if "sms" in alerts_dict:
            alerts.append(
                AlertMessage(
                    target_audience="sms",
                    language="en",
                    severity=request.severity.lower(),
                    message=alerts_dict["sms"],
                )
            )

        return CommunicationResponse(
            incident_id=request.incident_id,
            alerts=alerts,
            broadcast_ready=len(alerts) > 0,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert generation failed: {str(e)}")


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "communication_agent"}
