"""
Pipeline Orchestrator Service
Manages the flow of incidents through the entire disaster management pipeline:
Detection → Assessment → GIS → Resource → Route → Communication → Feedback → Prediction
"""

import json
import logging
import httpx
import os
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates incident flow through the complete disaster management pipeline.
    Manages state transitions, inter-agent communication, and data consistency.
    """

    def __init__(
        self,
        detection_url: str = "http://localhost:8000",
        assessment_url: str = "http://localhost:8001",
        disaster_agents_url: str = "http://localhost:8100",
        prediction_url: str = "http://localhost:8003",
        learning_url: str = "http://localhost:8004",
    ):
        """
        Initialize orchestrator with service URLs.

        Args:
            detection_url: Detection Agent API base URL
            assessment_url: Assessment Agent API base URL
            disaster_agents_url: Disaster Agents API base URL
            prediction_url: Prediction Agent API base URL
        """
        # Allow overriding service hosts via environment variables (Docker Compose)
        det_env = os.getenv("DETECTION_HOST") or os.getenv("DETECTION_URL")
        asm_env = os.getenv("ASSESSMENT_HOST") or os.getenv("ASSESSMENT_URL")
        dis_env = os.getenv("DISASTER_HOST") or os.getenv("DISASTER_URL")
        pred_env = os.getenv("PREDICTION_HOST") or os.getenv("PREDICTION_URL")
        learn_env = os.getenv("LEARNING_HOST") or os.getenv("LEARNING_URL")

        def _build_url(env_val, default):
            if env_val:
                if env_val.startswith("http"):
                    return env_val.rstrip("/")
                return f"http://{env_val.rstrip('/')}"
            return default

        self.detection_url = _build_url(det_env, detection_url)
        self.assessment_url = _build_url(asm_env, assessment_url)
        self.disaster_agents_url = _build_url(dis_env, disaster_agents_url)
        self.prediction_url = _build_url(pred_env, prediction_url)
        self.learning_url = _build_url(learn_env, learning_url)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def process_incident(self, detection_response: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """
        Process incident through the complete pipeline.
        Takes Detection output and routes it through all stages.

        Args:
            detection_response: Output from Detection Agent

        Returns:
            Complete incident state with all agent outputs
        """
        incident_id = detection_response.get("incident_id")
        logger.info(f"[Orchestrator] Processing incident {incident_id}")

        try:
            # Stage 1: Detection → Assessment
            logger.info(f"[Orchestrator] Stage 1/7: Triggering Assessment for {incident_id}")
            incident_state = await self._trigger_assessment(detection_response, on_stage)

            # Stage 2: Assessment → GIS Analysis
            logger.info(f"[Orchestrator] Stage 2/7: Triggering GIS Analysis for {incident_id}")
            incident_state = await self._trigger_gis_analysis(incident_state, on_stage)

            # Stage 3: GIS → Resource Allocation
            logger.info(f"[Orchestrator] Stage 3/7: Triggering Resource Allocation for {incident_id}")
            incident_state = await self._trigger_resource_allocation(incident_state, on_stage)

            # Stage 4: Resource → Route Optimization
            logger.info(f"[Orchestrator] Stage 4/7: Triggering Route Optimization for {incident_id}")
            incident_state = await self._trigger_route_optimization(incident_state, on_stage)

            # Stage 5: Route → Communication
            logger.info(f"[Orchestrator] Stage 5/7: Triggering Communication for {incident_id}")
            incident_state = await self._trigger_communication(incident_state, on_stage)

            # Stage 6: Initial Feedback (can happen in parallel with other stages)
            logger.info(f"[Orchestrator] Stage 6/7: Initializing Feedback for {incident_id}")
            incident_state = await self._initialize_feedback(incident_state, on_stage)

            # Stage 7: Prediction
            logger.info(f"[Orchestrator] Stage 7/7: Triggering Prediction for {incident_id}")
            incident_state = await self._trigger_prediction(incident_state, on_stage)

            # Stage 8: Learning
            logger.info(f"[Orchestrator] Stage 8/8: Triggering Learning for {incident_id}")
            incident_state = await self._trigger_learning(incident_state, on_stage)

            logger.info(f"[Orchestrator] Pipeline complete for {incident_id}")
            return incident_state

        except Exception as e:
            logger.error(f"[Orchestrator] Error processing {incident_id}: {str(e)}")
            raise

    async def _trigger_learning(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Trigger learning analysis and persist results to knowledge stores."""
        try:
            learning_input = {
                "incident_id": incident_state.get("incident_id"),
                "incident_type": incident_state.get("incident_type"),
                "incident_state": incident_state,
            }

            response = await self.client.post(
                f"{self.learning_url}/api/v1/learning/analyze",
                json=learning_input,
                timeout=60.0,
            )
            response.raise_for_status()
            learning_output = response.json()

            incident_state["learning_output"] = learning_output
            incident_state["pipeline_stage"] = "learning"
            # emit stage
            try:
                if on_stage:
                    if hasattr(on_stage, '__call__'):
                        maybe = on_stage( 'learning', learning_output)
                        if hasattr(maybe, '__await__'):
                            await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] Learning stage failed: {str(e)}")
            incident_state["learning_output"] = None
            return incident_state

    async def _trigger_assessment(self, detection_response: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Convert Detection output to Assessment input and trigger Assessment."""
        try:
            # Map Detection response to Assessment input
            assessment_input = {
                "incident_id": detection_response.get("incident_id"),
                "incident_type": detection_response.get("incident_type"),
                "location": detection_response.get("location"),
                "affected_population": detection_response.get("affected_population", 0),
                "confidence": detection_response.get("confidence", 0.0),
                "water_level": detection_response.get("water_level"),
                "source_count": detection_response.get("source_count", 1),
                "timestamp": detection_response.get("timestamp"),
            }

            # Call Assessment API
            try:
                response = await self.client.post(
                    f"{self.assessment_url}/api/v1/assessments/assess",
                    json=assessment_input,
                )
                response.raise_for_status()
                assessment_output = response.json()
            except Exception:
                # Fallback synthetic assessment when assessment service unavailable
                severity = detection_response.get('hazard_severity') or detection_response.get('severity') or 'Medium'
                affected = detection_response.get('affected_population') or detection_response.get('population') or 0
                risk_score = 0.5
                if severity and isinstance(severity, str) and severity.lower().startswith('high'):
                    risk_score = 0.85
                elif affected and affected > 5000:
                    risk_score = 0.75
                assessment_output = {
                    'severity': severity,
                    'priority': 'high' if risk_score>0.7 else 'medium',
                    'risk_score': risk_score,
                    'resource_urgency': 'high' if risk_score>0.7 else 'medium',
                    'escalation_required': risk_score>0.8,
                    'explanation': 'Synthetic assessment (demo): estimated from detection payload'
                }

            # Build unified incident state
            incident_state = {
                # Detection data
                **detection_response,
                # Assessment data
                "severity": assessment_output.get("severity"),
                "priority": assessment_output.get("priority"),
                "risk_score": assessment_output.get("risk_score"),
                "resource_urgency": assessment_output.get("resource_urgency"),
                "escalation_required": assessment_output.get("escalation_required"),
                "assessment_explanation": assessment_output.get("explanation"),
                "pipeline_stage": "assessment",
            }
            # emit stage
            try:
                if on_stage:
                    maybe = on_stage('assessment', assessment_output)
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.error(f"[Orchestrator] Assessment failed: {str(e)}")
            raise

    async def _trigger_gis_analysis(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Trigger GIS analysis using Assessment results."""
        try:
            # Map to GIS input
            gis_input = {
                "incident_id": incident_state.get("incident_id"),
                "incident_type": incident_state.get("incident_type"),
                "affected_population": incident_state.get("affected_population", 0),
                "latitude": incident_state.get("latitude", 0.0),
                "longitude": incident_state.get("longitude", 0.0),
                "hazard_severity": incident_state.get("severity", "Medium"),
                "population_density": "High" if incident_state.get("affected_population", 0) > 5000 else "Medium",
                "infrastructure_vulnerability": "Medium",  # TODO: infer from incident type
                "resource_availability": "Medium",
                "environmental_condition": "Medium",
            }

            # Call GIS API
            response = await self.client.post(
                f"{self.disaster_agents_url}/api/v1/gis/analyze",
                json=gis_input,
            )
            response.raise_for_status()
            gis_output = response.json()

            # Update incident state
            incident_state["gis_output"] = gis_output
            incident_state["pipeline_stage"] = "gis"
            try:
                if on_stage:
                    maybe = on_stage('gis', gis_output)
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] GIS analysis failed: {str(e)}")
            # Don't fail the pipeline
            incident_state["gis_output"] = None
            return incident_state

    async def _trigger_resource_allocation(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Trigger resource allocation using GIS results."""
        try:
            gis_output = incident_state.get("gis_output", {})
            
            # Map to Resource input
            resource_input = {
                "incident_id": incident_state.get("incident_id"),
                "incident_type": incident_state.get("incident_type"),
                "risk_probability": gis_output.get("risk_probability", 0.5),
                "affected_population": incident_state.get("affected_population", 0),
                "infrastructure_vulnerability": gis_output.get("infrastructure_vulnerability", "Medium"),
                "resource_availability": gis_output.get("resource_availability", "Medium"),
                "latitude": incident_state.get("latitude"),
                "longitude": incident_state.get("longitude"),
            }

            # Call Resource API
            response = await self.client.post(
                f"{self.disaster_agents_url}/api/v1/resource/allocate",
                json=resource_input,
            )
            response.raise_for_status()
            resource_output = response.json()

            # Update incident state
            incident_state["resource_output"] = resource_output
            incident_state["pipeline_stage"] = "resource"
            try:
                if on_stage:
                    maybe = on_stage('resource', resource_output)
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] Resource allocation failed: {str(e)}")
            try:
                import traceback
                traceback.print_exc()
            except Exception:
                pass
            incident_state["resource_output"] = None
            return incident_state

    async def _trigger_route_optimization(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Trigger route optimization using Resource results."""
        try:
            # Map to Route input
            route_input = {
                "incident_id": incident_state.get("incident_id"),
                "incident_location": incident_state.get("location"),
                "incident_lat": incident_state.get("latitude"),
                "incident_lon": incident_state.get("longitude"),
                "available_resources": [
                    "doon_hospital",
                    "ndrf_camp",
                    "coronation_hospital",
                ],  # TODO: lookup actual resources
            }

            # Call Route API
            response = await self.client.post(
                f"{self.disaster_agents_url}/api/v1/route/optimize",
                json=route_input,
            )
            response.raise_for_status()
            route_output = response.json()

            # Update incident state
            incident_state["route_output"] = route_output
            incident_state["pipeline_stage"] = "route"
            try:
                if on_stage:
                    maybe = on_stage('route', route_output)
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] Route optimization failed: {str(e)}")
            incident_state["route_output"] = None
            return incident_state

    async def _trigger_communication(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Trigger communication using all previous results."""
        try:
            # Map to Communication input
            comm_input = {
                "incident_id": incident_state.get("incident_id"),
                "incident_type": incident_state.get("incident_type"),
                "location": incident_state.get("location"),
                "latitude": incident_state.get("latitude"),
                "longitude": incident_state.get("longitude"),
                "affected_population": incident_state.get("affected_population", 0),
                "severity": incident_state.get("severity", "Medium"),
                "risk_score": incident_state.get("risk_score", 50),
            }

            # Call Communication API
            response = await self.client.post(
                f"{self.disaster_agents_url}/api/v1/communication/generate-alerts",
                json=comm_input,
            )
            response.raise_for_status()
            comm_output = response.json()

            # Update incident state
            incident_state["communication_output"] = comm_output
            incident_state["pipeline_stage"] = "communication"
            try:
                if on_stage:
                    maybe = on_stage('communication', comm_output)
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] Communication failed: {str(e)}")
            incident_state["communication_output"] = None
            return incident_state

    async def _initialize_feedback(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Initialize feedback tracking for the incident."""
        try:
            # No specific call needed, just mark feedback as active
            incident_state["feedback_output"] = {
                "incident_id": incident_state.get("incident_id"),
                "total_feedback_count": 0,
                "corroborated": False,
                "average_trust_score": 0.0,
                "recommended_actions": [],
                "statistics": {},
            }
            try:
                if on_stage:
                    maybe = on_stage('feedback', incident_state.get('feedback_output'))
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] Feedback initialization failed: {str(e)}")
            return incident_state

    async def _trigger_prediction(self, incident_state: Dict[str, Any], on_stage=None) -> Dict[str, Any]:
        """Trigger prediction using all agent outputs."""
        try:
            # Map to Prediction input
            prediction_input = {
                "incident_id": incident_state.get("incident_id"),
                "incident_type": incident_state.get("incident_type"),
                "detection_output": {
                    "confidence": incident_state.get("confidence"),
                    "affected_population": incident_state.get("affected_population"),
                    "casualties": incident_state.get("casualties"),
                },
                "assessment_output": {
                    "severity": incident_state.get("severity"),
                    "risk_score": incident_state.get("risk_score"),
                },
                "gis_output": incident_state.get("gis_output"),
                "resource_output": incident_state.get("resource_output"),
            }

            # Call Prediction API
            response = await self.client.post(
                f"{self.prediction_url}/api/v1/predict",
                json=prediction_input,
                timeout=60.0,
            )
            response.raise_for_status()
            prediction_output = response.json()

            # Update incident state
            incident_state["prediction_output"] = prediction_output
            incident_state["pipeline_stage"] = "prediction"
            try:
                if on_stage:
                    maybe = on_stage('prediction', prediction_output)
                    if hasattr(maybe, '__await__'):
                        await maybe
            except Exception:
                pass
            return incident_state

        except Exception as e:
            logger.warning(f"[Orchestrator] Prediction failed: {str(e)}")
            incident_state["prediction_output"] = None
            return incident_state
