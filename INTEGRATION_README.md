# Disaster Management Platform - Integrated Pipeline

This repository contains a fully integrated Disaster Management Platform that processes incidents through a complete pipeline:

```
Detection Agent
    ↓
Assessment Agent
    ↓
GIS Agent
    ↓
Resource Agent
    ↓
Route Agent
    ↓
Communication Agent
    ↓
Feedback Agent
    ↓
Prediction Agent
```

## Architecture Overview

### Core Agents

1. **Detection Agent** (Port 8000)
   - Detects and classifies disasters from multiple sources
   - Outputs: `DetectionResponse` with incident details, confidence, urgency
   - **API Endpoint**: `POST /api/v1/detect/detect`

2. **Assessment Agent** (Port 8001)
   - Evaluates severity, risk, and resource requirements
   - Consumes: Detection output
   - Outputs: Severity, priority, risk_score, resource recommendations
   - **API Endpoint**: `POST /api/v1/assessments/assess`

3. **GIS Agent** (Port 8002)
   - Analyzes spatial risk using Bayesian CPT-based methods
   - Consumes: Assessment output
   - Outputs: Risk probability, affected radius, infrastructure vulnerability
   - **API Endpoint**: `POST /api/v1/gis/analyze`

4. **Resource Agent** (Port 8002)
   - Allocates resources based on risk and population
   - Consumes: GIS output
   - Outputs: Priority score, required resources, deployment order
   - **API Endpoint**: `POST /api/v1/resource/allocate`

5. **Route Agent** (Port 8002)
   - Optimizes delivery routes using A* algorithm
   - Consumes: Resource output
   - Outputs: Routes, ETAs, recommendations
   - **API Endpoint**: `POST /api/v1/route/optimize`

6. **Communication Agent** (Port 8002)
   - Generates multilingual alerts (English + Hindi)
   - Consumes: Route output
   - Outputs: Alerts for citizens, authorities, SMS
   - **API Endpoint**: `POST /api/v1/communication/generate-alerts`

7. **Feedback Agent** (Port 8002)
   - Collects and validates field/citizen feedback
   - Consumes: Communication output
   - Outputs: Trust scores, corroboration, recommended actions
   - **API Endpoint**: `POST /api/v1/feedback/submit`

8. **Prediction Agent** (Port 8003)
   - Predicts escalation probability and resource needs
   - Consumes: All previous agent outputs
   - Outputs: Escalation probability, predicted severity, resource forecast
   - **API Endpoint**: `POST /api/v1/predict`

## Integration Architecture

### Pipeline Orchestrator

The `PipelineOrchestrator` (in `shared/orchestrator.py`) manages the complete flow:

1. **Automatic Triggering**: When a `DetectionResponse` is generated, the orchestrator automatically:
   - Triggers Assessment → GIS → Resource → Route → Communication → Feedback → Prediction
   - Maintains unified incident state across all stages
   - Handles failures gracefully (non-blocking)

2. **Data Flow**:
   ```
   Detection output (DetectionResponse)
       ↓ [mapped to IncidentInput]
   Assessment (IncidentInput → AssessmentResponse)
       ↓ [extracted fields from assessment]
   GIS Analysis (GISAnalysisRequest → GISRiskOutput)
       ↓ [uses risk probability]
   Resource Allocation (ResourceAllocationRequest → ResourceDeploymentPlan)
       ↓ [uses priority score]
   Route Optimization (RouteOptimizationRequest → RouteOptimizationResponse)
       ↓ [provides routing]
   Communication (CommunicationRequest → CommunicationResponse)
       ↓ [validates feedback]
   Feedback (FeedbackSubmission → analysis)
       ↓ [feeds historical data]
   Prediction (PredictionRequest → PredictionResponse)
   ```

### Unified Data Model

All incidents flow through a unified `IncidentState` that includes:

- Detection fields: incident_id, type, location, coordinates, affected_population, confidence
- Assessment fields: severity, priority, risk_score, escalation_required
- GIS fields: risk_probability, affected_radius, infrastructure_vulnerability
- Resource fields: priority_score, required_resources, availability_status
- Route fields: routes, fastest_route, ETAs
- Communication fields: alerts, languages, audiences
- Feedback fields: corroboration, trust_scores, recommended_actions
- Prediction fields: escalation_probability, predicted_severity, resource_forecast

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose -f docker-compose.full.yml up -d
```

This starts:
- Detection Agent (8000)
- Assessment Agent (8001)
- Disaster Agents API (8002) - GIS, Resource, Route, Communication, Feedback
- Prediction Agent (8003)
- Ollama LLM backend (11434)

### Manual Deployment

**Detection Agent**:
```bash
cd Detection_agent
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Assessment Agent**:
```bash
cd Assessment_agent/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Disaster Agents API**:
```bash
pip install -r Disaster_agent_api/requirements.txt
python -m uvicorn Disaster_agent_api.main:app --host 0.0.0.0 --port 8002
```

**Prediction Agent**:
```bash
pip install -r Prediction_agent/requirements.txt
python -m uvicorn Prediction_agent.main:app --host 0.0.0.0 --port 8003
```

## Usage Examples

### 1. Submit Incident for Full Pipeline Processing

```bash
curl -X POST http://localhost:8000/api/v1/detect/detect \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_report",
    "content": "Major flood detected in Dehradun area with 5000 people affected",
    "timestamp": "2024-01-15T10:30:00Z",
    "language": "en",
    "metadata": {
      "author": "News Reporter",
      "channel": "Local News",
      "location_hint": "Dehradun, India"
    }
  }'
```

**Response**: Incident detected and full pipeline triggered automatically

```json
{
  "incident_id": "INC-2024-001",
  "incident_type": "Flood",
  "location": "Dehradun, India",
  "latitude": 30.1975,
  "longitude": 78.0615,
  "affected_population": 5000,
  "casualties": 0,
  "urgency": "High",
  "confidence": 0.87,
  "extraction_debug": { ... }
}
```

The orchestrator then automatically:
1. Triggers Assessment (evaluates severity/priority)
2. Triggers GIS (analyzes risk zones)
3. Triggers Resource (allocates resources)
4. Triggers Route (optimizes delivery)
5. Triggers Communication (generates alerts)
6. Triggers Prediction (forecasts escalation)

### 2. Query Detection Results

```bash
curl http://localhost:8000/api/v1/incidents/?incident_type=Flood
```

### 3. View Assessment Results

```bash
curl http://localhost:8001/api/v1/assessments/history?limit=10
```

### 4. Get GIS Analysis

```bash
curl -X POST http://localhost:8002/api/v1/gis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "affected_population": 5000,
    "latitude": 30.1975,
    "longitude": 78.0615,
    "hazard_severity": "High",
    "population_density": "High",
    "infrastructure_vulnerability": "Medium"
  }'
```

### 5. Get Resource Allocation

```bash
curl -X POST http://localhost:8002/api/v1/resource/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "risk_probability": 0.8,
    "affected_population": 5000,
    "infrastructure_vulnerability": "Medium",
    "resource_availability": "Medium"
  }'
```

### 6. Get Route Optimization

```bash
curl -X POST http://localhost:8002/api/v1/route/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_location": "Dehradun",
    "incident_lat": 30.1975,
    "incident_lon": 78.0615,
    "available_resources": ["doon_hospital", "ndrf_camp", "coronation_hospital"]
  }'
```

### 7. Generate Communication Alerts

```bash
curl -X POST http://localhost:8002/api/v1/communication/generate-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "location": "Dehradun",
    "latitude": 30.1975,
    "longitude": 78.0615,
    "affected_population": 5000,
    "severity": "High"
  }'
```

### 8. Submit Feedback

```bash
curl -X POST http://localhost:8002/api/v1/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "feedback_type": "Route Blocked",
    "source_type": "NDRF Responder",
    "message": "Rajpur Road is blocked by debris",
    "road": "Rajpur Rd"
  }'
```

### 9. Get Prediction

```bash
curl -X POST http://localhost:8003/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "detection_output": {
      "confidence": 0.87,
      "affected_population": 5000,
      "casualties": 0
    },
    "assessment_output": {
      "severity": "High",
      "risk_score": 85
    },
    "gis_output": {
      "risk_probability": 0.8,
      "affected_radius_km": 5.0,
      "infrastructure_vulnerability": "Medium",
      "resource_availability": "Medium"
    }
  }'
```

**Response**:
```json
{
  "incident_id": "INC-2024-001",
  "escalation_probability": 0.72,
  "predicted_severity": "High",
  "population_impact": 7500,
  "infrastructure_impact": 0.65,
  "resource_forecast": {
    "ambulances": 10,
    "rescue_teams": 8,
    "boats": 10
  },
  "recommended_actions": [
    "ESCALATE: Activate emergency response level 2",
    "REQUEST: Additional resources from neighboring districts",
    "EVACUATE: Begin evacuation of affected areas",
    "PREPARE: Set up emergency shelters and aid centers",
    "MONITOR: Set up continuous incident monitoring",
    "COMMUNICATE: Update public every 30 minutes"
  ],
  "confidence": 0.80,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

## Directory Structure

```
DISASTER DETECTION AGENT/
├── shared/                      # Shared components across all agents
│   ├── schemas.py              # Unified schemas for all agents
│   ├── database_models.py       # Unified database models
│   └── orchestrator.py          # Pipeline orchestrator
├── Detection_agent/             # Detection Agent
│   ├── app/
│   ├── tests/
│   └── main.py
├── Assessment_agent/            # Assessment Agent
│   ├── backend/
│   └── docker-compose.yml
├── Disaster_agent_api/          # Unified Disaster Agents API
│   ├── routes/
│   │   ├── gis_routes.py
│   │   ├── resource_routes.py
│   │   ├── route_routes.py
│   │   ├── communication_routes.py
│   │   └── feedback_routes.py
│   └── main.py
├── Prediction_agent/            # Prediction Agent
│   ├── prediction_engine.py
│   └── main.py
├── Disaster/                    # Original Disaster agents
│   ├── agents/
│   │   ├── gis_agent.py
│   │   ├── resource_agent.py
│   │   ├── route_agent.py
│   │   ├── communication_agent.py
│   │   └── feedback_agent.py
│   └── data/
├── tests/                       # Integration tests
│   └── test_integration.py
└── docker-compose.full.yml      # Docker compose for full stack
```

## Testing

### Run Integration Tests

```bash
pip install pytest pytest-asyncio
pytest tests/test_integration.py -v
```

### Test Individual Components

```bash
# Test Prediction Engine
python -m pytest tests/test_integration.py::test_prediction_engine_basic -v

# Test High Escalation Scenario
python -m pytest tests/test_integration.py::test_prediction_high_escalation -v

# Test Low Escalation Scenario
python -m pytest tests/test_integration.py::test_prediction_low_escalation -v
```

## Performance Characteristics

- **Detection**: ~2-3 seconds per incident
- **Assessment**: ~1-2 seconds
- **GIS Analysis**: ~500ms
- **Resource Allocation**: ~200ms
- **Route Optimization**: ~1-2 seconds (A*)
- **Communication**: ~500ms
- **Prediction**: ~500ms
- **Total E2E**: ~8-11 seconds per incident

## Scaling Considerations

1. **Database**: Unified model supports SQLite for development, PostgreSQL for production
2. **Async Processing**: All agents run in background after initial detection
3. **Load Balancing**: Deploy multiple instances behind load balancer
4. **Message Queue**: Can add Kafka/RabbitMQ for event streaming
5. **Caching**: Qdrant vector DB for similarity search
6. **Monitoring**: Structured logging for all pipeline stages

## Key Features

✅ Automatic pipeline triggering  
✅ Non-blocking agent failures (pipeline continues)  
✅ Unified incident state across all agents  
✅ Multilingual alerts (English + Hindi)  
✅ Bayesian risk assessment  
✅ A* route optimization  
✅ Resource allocation based on risk  
✅ Feedback validation with trust scoring  
✅ Escalation probability prediction  
✅ Comprehensive logging and audit trail  

## Contributing

To add a new agent or modify existing ones:

1. Follow the unified schema in `shared/schemas.py`
2. Add route in appropriate `*_routes.py` file
3. Update orchestrator in `shared/orchestrator.py` if needed
4. Add tests in `tests/test_integration.py`
5. Update docker-compose if adding new service

## License

See LICENSE file in repository root.
