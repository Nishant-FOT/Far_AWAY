"""
Feedback Agent API wrapper.
Exposes the existing Feedback agent as a REST endpoint.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import the existing Feedback agent
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../Disaster'))

from agents.feedback_agent import FeedbackAgent

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

# Singleton instance
_feedback_agent = FeedbackAgent()


# ─────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ─────────────────────────────────────────────────────────────────────


class FeedbackSubmission(BaseModel):
    """Single feedback report."""
    incident_id: str
    feedback_type: str
    source_type: str
    message: str
    location: Optional[str] = None
    road: Optional[str] = None


class RecommendedAction(BaseModel):
    """Recommended action from feedback analysis."""
    action_type: str
    target: Optional[str] = None
    confidence: float
    reason: str


class FeedbackAnalysisResponse(BaseModel):
    """Response from feedback analysis."""
    incident_id: str
    total_feedback_count: int
    corroborated: bool
    average_trust_score: float
    recommended_actions: List[RecommendedAction]
    statistics: dict
    timestamp: datetime = None


# ─────────────────────────────────────────────────────────────────────
# Feedback Endpoints
# ─────────────────────────────────────────────────────────────────────


@router.post("/submit")
async def submit_feedback(feedback: FeedbackSubmission):
    """Submit feedback report from field or citizens."""
    try:
        # Call submit using existing agent
        result = _feedback_agent.submit(
            incident_id=feedback.incident_id,
            feedback_type=feedback.feedback_type,
            description=feedback.message,
            source=feedback.source_type,
            location=feedback.location,
            road=feedback.road,
        )

        return {
            "status": "submitted",
            "incident_id": feedback.incident_id,
            "feedback_id": result.get("id"),
            "recommended_action": result.get("recommended_action"),
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "feedback_agent"}
