# Emergency Response Agent - Complete Documentation

A fully integrated, production-ready disaster management and emergency response platform with intelligent incident detection, assessment, spatial analysis, resource allocation, route optimization, and predictive analytics.

WE WERE UNABLE TO UPLOAD THE COMPLETE PROJECT ON GITHUB , SO HERE IS THE COMPLETE PROJECT LINK - https://drive.google.com/file/d/1mbr3kHPyFdByAtMhMtdGjEcvcEcU1kvu/view?usp=sharing

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Prerequisites & Installation](#prerequisites--installation)
5. [Running the System](#running-the-system)
6. [API Endpoints & Usage](#api-endpoints--usage)
7. [Data Schemas](#data-schemas)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Testing](#testing)

---

## Project Overview

The **Emergency Response Agent** is an intelligent disaster management system that automatically processes emergency incidents through an 8-stage orchestrated pipeline:

**Detection → Assessment → GIS Analysis → Resource Allocation → Route Optimization → Communication → Feedback → Prediction**

### Key Capabilities

- **Real-time Incident Detection**: Process incidents from multiple sources (news, social media, sensor data, user reports)
- **Intelligent Assessment**: Evaluate severity, priority, and risk scores
- **Spatial Analysis**: Bayesian risk modeling with affected radius calculation
- **Resource Optimization**: Smart allocation based on incident severity and population impact
- **Route Planning**: A* pathfinding with dynamic weighting considering risk and damage
- **Multilingual Communication**: Generate alerts in English and Hindi
- **Feedback Validation**: Trust scoring and corroboration analysis
- **Predictive Analytics**: Forecast escalation probability and resource needs

### Deployment Target

- **Hackathon-friendly**: Low-resource requirements, open-source stack
- **Production-ready**: Docker containerization, comprehensive error handling
- **Cloud-native**: Supports deployment on cloud platforms

---

## Architecture Overview

### 8-Stage Orchestrated Pipeline

```
User Input (text, sensor, news, social)
    ↓
1. DETECTION AGENT (Port 8000)
   Entity Extraction, Rule Engine, LLM Classifier, Geocoding
    ↓
2. ASSESSMENT AGENT (Port 8001)
   Severity Engine, Risk Engine, Resource Engine, Escalation Check
    ↓
3. GIS AGENT (Port 8002)
   Bayesian Risk Analysis, Affected Radius, Infrastructure Vulnerability
    ↓
4. RESOURCE AGENT (Port 8002)
   Priority Scoring, Allocation Planning, Availability Tracking
    ↓
5. ROUTE AGENT (Port 8002)
   A* Pathfinding, Dynamic Weighting, ETA Calculation
    ↓
6. COMMUNICATION AGENT (Port 8002)
   Multilingual Alerts (EN/HI), Audience-specific Messaging
    ↓
7. FEEDBACK AGENT (Port 8002)
   Trust Scoring, Duplicate Detection, Corroboration Analysis
    ↓
8. PREDICTION AGENT (Port 8003)
   Escalation Forecasting, Severity Prediction, Resource Forecast
    ↓
ACTIONABLE INTELLIGENCE
```

### Unified Incident State

All incidents flow through a unified state containing:

- **Detection fields**: incident_id, type, location, coordinates, affected_population, confidence
- **Assessment fields**: severity, priority, risk_score, escalation_required
- **GIS fields**: risk_probability, affected_radius, infrastructure_vulnerability
- **Resource fields**: priority_score, required_resources, availability_status
- **Route fields**: routes, fastest_route, ETAs
- **Communication fields**: alerts, languages, audiences
- **Feedback fields**: corroboration, trust_scores, recommended_actions
- **Prediction fields**: escalation_probability, predicted_severity, resource_forecast

---

## Core Components

### 1. Detection Agent (Port 8000)

Identifies and classifies disasters from multiple sources.

**Technologies**: GLiNER entity extraction, Rule-based heuristics, LLM (Ollama), Nominatim geocoding

**Features**:
- Multi-source support (news, social media, sensors, user reports)
- Real-time geocoding
- Confidence scoring (0-1)
- Fallback rule-based detection
- Language support
- Sensor data integration

**Key Endpoints**:
- POST /api/v1/detect/detect - Single incident detection
- POST /api/v1/detect/detect/batch - Batch detection
- GET /api/v1/incidents - Incident history

### 2. Assessment Agent (Port 8001)

Evaluates severity, risk, and resource requirements.

**Decision Pipeline**:
1. Severity Assessment Engine
2. Risk Scoring Engine (0-100)
3. Resource Recommendation Engine
4. Escalation Check Engine
5. Optional LLM Explanation

**Resources Tracked**: Ambulances, Rescue teams, Fire units, Police units, Medical teams, Shelters, Boats

**Key Endpoints**:
- POST /api/v1/assessments/assess - Assess incident
- GET /api/v1/assessments/history - Assessment history
- GET /api/v1/assessments/health - Health check

### 3. GIS Agent (Port 8002)

Spatial risk analysis using Bayesian inference.

**Capabilities**:
- CPT-based Bayesian probability modeling
- Affected radius calculation (km)
- Infrastructure vulnerability assessment
- Risk probability (0-1) scoring
- Spatial pattern analysis

**Key Endpoint**: POST /api/v1/gis/analyze

### 4. Resource Agent (Port 8002)

Smart allocation of emergency resources.

**Outputs**:
- Priority scores for incident severity
- Resource allocation plan
- Availability status
- Shortage identification

**Key Endpoint**: POST /api/v1/resource/allocate

### 5. Route Agent (Port 8002)

Optimize delivery and emergency response routes.

**Algorithm**: A* pathfinding with Haversine distance calculation

**Dynamic Weighting**:
- Traffic conditions
- Flood risk levels
- Road damage severity
- Infrastructure status

**Outputs**: Multiple route options, fastest route, ETA calculations

**Key Endpoint**: POST /api/v1/route/optimize

### 6. Communication Agent (Port 8002)

Generate multilingual emergency alerts.

**Features**:
- Bilingual support (English + Hindi)
- Audience-specific messaging (citizen, authority, SMS)
- Disaster-specific safety advice
- Real-time alert distribution
- Template-based message generation

**Key Endpoint**: POST /api/v1/communication/generate-alerts

### 7. Feedback Agent (Port 8002)

Validation and corroboration of incident data.

**Trust Scoring by Source**:
- Control Room: 0.95
- NDRF Responder: 0.93
- Police Officer: 0.85
- Citizen: 0.55
- Social Media: 0.35

**Features**:
- Duplicate detection (10-minute windows)
- Trust scoring
- Corroboration analysis
- Feedback aggregation
- Action evaluation

**Key Endpoint**: POST /api/v1/feedback/submit

### 8. Prediction Agent (Port 8003)

Forecast escalation and resource needs.

**Predictions**:
- Escalation Probability (0-1): Risk of incident worsening
- Predicted Severity: High/Medium/Low with confidence
- Population Impact: Estimated affected population
- Infrastructure Impact: Proportion at risk (0-1)
- Resource Forecast: Recommended allocations
- Recommended Actions: Prioritized action list

**Signals Used**:
- GIS risk probability
- Assessment risk score
- Affected population
- Infrastructure vulnerability
- Resource availability
- Incident type modifiers

**Key Endpoint**: POST /api/v1/predict

---

## Prerequisites & Installation

### System Requirements

- Docker Desktop or Docker Engine with docker-compose
- Node.js 18+ (for local frontend development)
- Python 3.10/3.11 (for local backend development - optional)
- RAM: 8GB recommended
- Available Ports: 8000-8004, 3000, 11434

### Environment Setup

1. Navigate to repository:

```bash
cd "c:\Users\hp\Desktop\INTERNATIONAL NO 1\ROUND 1\DISASTER DETECTION AGENT"
```

2. Create environment file (if needed):

```bash
cp .env.example .env
```

---

## Running the System

### Option 1: Docker Compose (Recommended)

#### Quick Start (All Services)

```bash
# From repository root
docker-compose -f docker-compose.full.yml pull
docker-compose -f docker-compose.full.yml build --no-cache
docker-compose -f docker-compose.full.yml up -d
```

#### Verify Services Are Running

```bash
# Check all services
docker-compose -f docker-compose.full.yml ps

# Check specific service logs
docker-compose -f docker-compose.full.yml logs -f detection_agent
docker-compose -f docker-compose.full.yml logs -f assessment_agent
docker-compose -f docker-compose.full.yml logs -f disaster_agents
docker-compose -f docker-compose.full.yml logs -f prediction_agent
```

#### Health Checks

```bash
# PowerShell
curl.exe http://localhost:8000/api/v1/health
Invoke-RestMethod -Uri http://localhost:8001/api/v1/assessments/health

# Linux/Mac
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/assessments/health
```

#### Stop All Services

```bash
docker-compose -f docker-compose.full.yml down --volumes --remove-orphans
```

### Option 2: Manual Setup (Development)

Run each service in a separate terminal:

**Terminal 1 - Detection Agent (Port 8000)**:
```bash
cd Detection_agent
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Assessment Agent (Port 8001)**:
```bash
cd Assessment_agent/backend
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 3 - Disaster Agents (Port 8002)**:
```bash
python -m uvicorn Disaster_agent_api.main:app --reload --port 8002
```

**Terminal 4 - Prediction Agent (Port 8003)**:
```bash
cd Prediction_agent
python -m uvicorn main:app --reload --port 8003
```

**Terminal 5 - Learning Agent (Port 8004 - Optional)**:
```bash
python -m uvicorn Learning_agent.main:app --reload --port 8004
```

**Terminal 6 - Ollama (Port 11434 - Recommended)**:
```bash
ollama serve
```

### Option 3: Frontend Local Development

```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

---

## API Endpoints & Usage

### Detection Agent (Port 8000)

#### Detect Single Incident

**Endpoint**: `POST /api/v1/detect/detect`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/detect/detect \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "user_report",
    "content": "Heavy flooding in Dehradun with thousands affected",
    "timestamp": "2024-01-15T10:30:00Z",
    "language": "en",
    "metadata": {
      "author": "Field Reporter",
      "channel": "WhatsApp",
      "location_hint": "Dehradun, Uttarakhand"
    }
  }'
```

**Response**:
```json
{
  "incident_id": "INC-2024-001",
  "incident_type": "Flood",
  "location": "Dehradun",
  "latitude": 30.1975,
  "longitude": 78.0615,
  "affected_population": 5000,
  "urgency": "High",
  "confidence": 0.85
}
```

#### Other Endpoints

- `POST /api/v1/detect/detect/batch` - Batch incident detection
- `GET /api/v1/incidents` - Get incidents history
- `GET /api/v1/incidents/summary` - Get incidents summary
- `GET /api/v1/incidents/{incident_id}` - Get specific incident
- `GET /api/v1/health` - Health check

---

### Assessment Agent (Port 8001)

#### Assess Incident

**Endpoint**: `POST /api/v1/assessments/assess`

**Request**:
```bash
curl -X POST http://localhost:8001/api/v1/assessments/assess \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "location": "Dehradun",
    "affected_population": 5000,
    "confidence": 0.85
  }'
```

**Response**:
```json
{
  "incident_id": "INC-2024-001",
  "severity": "High",
  "priority": "P2",
  "risk_score": 75,
  "resource_urgency": "Urgent",
  "escalation_required": true,
  "recommended_resources": {
    "ambulances": 5,
    "rescue_teams": 4,
    "fire_units": 2,
    "police_units": 3,
    "medical_teams": 2,
    "shelters": 3
  }
}
```

#### Other Endpoints

- `POST /api/v1/assessments/assess/batch` - Batch assessment
- `GET /api/v1/assessments/history` - Assessment history
- `GET /api/v1/assessments/dashboard` - Dashboard summary
- `GET /api/v1/assessments/health` - Health check

---

### Disaster Agents (Port 8002)

#### 1. GIS Analysis

**Endpoint**: `POST /api/v1/gis/analyze`

#### 2. Resource Allocation

**Endpoint**: `POST /api/v1/resource/allocate`

#### 3. Route Optimization

**Endpoint**: `POST /api/v1/route/optimize`

#### 4. Communication Alerts

**Endpoint**: `POST /api/v1/communication/generate-alerts`

#### 5. Feedback Submission

**Endpoint**: `POST /api/v1/feedback/submit`

---

### Prediction Agent (Port 8003)

#### Predict Escalation

**Endpoint**: `POST /api/v1/predict`

**Request**:
```bash
curl -X POST http://localhost:8003/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "detection_output": {
      "confidence": 0.85,
      "affected_population": 5000,
      "casualties": 0
    },
    "assessment_output": {
      "severity": "High",
      "risk_score": 87
    },
    "gis_output": {
      "risk_probability": 0.8,
      "affected_radius_km": 5.0,
      "infrastructure_vulnerability": "Medium"
    }
  }'
```

**Response**:
```json
{
  "incident_id": "INC-2024-001",
  "escalation_probability": 0.75,
  "predicted_severity": "High",
  "population_impact": 7500,
  "infrastructure_impact": 0.64,
  "resource_forecast": {...},
  "recommended_actions": ["Deploy rescue teams", "Evacuate zone"]
}
```

---

## Data Schemas

### DetectionRequest

```json
{
  "source_type": "user_report|news_report|social_media|sensor_data",
  "source_id": "optional_source_id",
  "content": "Incident description (min 3 chars)",
  "timestamp": "2024-01-15T10:30:00Z",
  "language": "en",
  "metadata": {
    "author": "Reporter name",
    "channel": "Communication channel",
    "location_hint": "Geographic hint"
  },
  "sensor_data": {
    "water_level": 2.5,
    "rainfall": 45.2,
    "temperature": 22.5
  }
}
```

### AssessmentResponse

```json
{
  "incident_id": "INC-2024-001",
  "severity": "Critical|High|Medium|Low",
  "priority": "P1|P2|P3|P4",
  "risk_score": 75,
  "resource_urgency": "Immediate|Urgent|High|Normal",
  "escalation_required": true,
  "recommended_resources": {...},
  "explanation": "Human-readable explanation"
}
```

### PredictionResponse

```json
{
  "incident_id": "INC-2024-001",
  "escalation_probability": 0.75,
  "predicted_severity": "High",
  "population_impact": 7500,
  "infrastructure_impact": 0.64,
  "resource_forecast": {...},
  "recommended_actions": [...]
}
```

---

## Configuration

### Environment Variables

Create `.env` file in root directory:

```env
# Detection Agent
DETECTION_AGENT_PORT=8000
DETECTION_AGENT_HOST=0.0.0.0

# Assessment Agent
ASSESSMENT_AGENT_PORT=8001
ASSESSMENT_AGENT_HOST=0.0.0.0

# Disaster Agents
DISASTER_AGENTS_PORT=8002
DISASTER_AGENTS_HOST=0.0.0.0

# Prediction Agent
PREDICTION_AGENT_PORT=8003
PREDICTION_AGENT_HOST=0.0.0.0

# Learning Agent
LEARNING_AGENT_PORT=8004
LEARNING_AGENT_HOST=0.0.0.0

# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen:4b

# Database
DATABASE_URL=sqlite:///incidents.db
QDRANT_URL=http://qdrant:6333

# Features
ENABLE_LLM=true
ENABLE_QDRANT=false
DEMO_MODE=false
```

---

## Troubleshooting

### Port Already in Use

**Windows PowerShell**:
```bash
Get-NetTCPConnection -LocalPort 8000 | Select-Object -Property State, OwningProcess
Stop-Process -Id <PID> -Force
```

**Linux/Mac**:
```bash
lsof -i :8000
kill -9 <PID>
```

### Docker Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.full.yml logs -f service_name

# Rebuild without cache
docker-compose -f docker-compose.full.yml build --no-cache

# Remove dangling containers
docker-compose -f docker-compose.full.yml down -v
```

### Health Check Failing

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/assessments/health
```

### LLM/Ollama Issues

```bash
# Pull model
ollama pull qwen:4b

# Check running models
ollama list

# Test Ollama directly
curl http://localhost:11434/api/tags
```

### Database Errors

```bash
# Reset database (WARNING: deletes all data)
rm -f incidents.db
docker-compose -f docker-compose.full.yml up -d
```

---

## Testing

### Run Integration Tests

```bash
# From repository root
pytest -q
pytest -v  # Verbose output
pytest -s  # Show print statements
```

### Manual Test Flow

**Step 1: Submit Incident**
```bash
curl -X POST http://localhost:8000/api/v1/detect/detect \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_report",
    "content": "Major earthquake reported in Dehradun region",
    "timestamp": "2024-01-15T10:30:00Z",
    "language": "en"
  }'
```

**Step 2: Wait for Processing** (8-11 seconds for full pipeline)

**Step 3: Check Assessment**
```bash
curl http://localhost:8001/api/v1/assessments/history?limit=1
```

**Step 4: Get Prediction**
```bash
curl -X POST http://localhost:8003/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## File Structure

```
DISASTER DETECTION AGENT/
├── EMERGENCY_RESPONSE_AGENT.md         (This comprehensive guide)
├── requirements.txt                     (Shared dependencies)
├── docker-compose.full.yml              (Full stack orchestration)
├── pytest.ini                           (Test configuration)
│
├── Detection_agent/                     (Port 8000)
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/detection.py
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── Assessment_agent/                    (Port 8001)
│   └── backend/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   ├── services/
│       │   └── models/
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
│
├── Disaster_agent_api/                  (Port 8002)
│   ├── main.py
│   ├── routes/
│   │   ├── gis_routes.py
│   │   ├── resource_routes.py
│   │   ├── route_routes.py
│   │   ├── communication_routes.py
│   │   └── feedback_routes.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── Prediction_agent/                    (Port 8003)
│   ├── main.py
│   ├── prediction_engine.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── Learning_agent/                      (Port 8004 - Optional)
│   ├── main.py
│   ├── learning_engine.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                            (Next.js, Port 3000)
│   ├── pages/
│   ├── components/
│   ├── styles/
│   ├── package.json
│   ├── Dockerfile
│   └── tsconfig.json
│
├── shared/                              (Shared utilities)
│   ├── schemas.py                       (Unified schemas)
│   ├── database_models.py               (Unified DB models)
│   ├── orchestrator.py                  (Pipeline orchestrator)
│   └── requirements.txt
│
├── data/                                (Data storage)
│   ├── raw/
│   ├── synthetic/
│   ├── annotated/
│   └── final/
│
└── tests/                               (Integration tests)
    └── test_integration.py
```

---

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Detection Agent | 8000 | Incident detection & classification |
| Assessment Agent | 8001 | Severity & risk assessment |
| Disaster Agents | 8002 | GIS, Resource, Route, Communication, Feedback |
| Prediction Agent | 8003 | Predictive analytics |
| Learning Agent | 8004 | Model learning (optional) |
| Frontend | 3000 | UI Dashboard |
| Ollama | 11434 | LLM Server |

---

## Key Features

### Detection
- Multi-source incident detection
- Real-time entity extraction
- Geocoding with Nominatim
- Confidence scoring

### Assessment
- Deterministic severity assessment
- Risk scoring (0-100)
- Resource recommendations
- Escalation detection

### GIS
- Bayesian risk modeling
- Affected radius calculation
- Infrastructure vulnerability

### Resource Allocation
- Priority scoring
- Resource allocation planning
- Availability tracking
- Shortage identification

### Route Optimization
- A* pathfinding
- Dynamic route weighting
- ETA calculation

### Communication
- Multilingual alerts (EN/HI)
- Audience-specific messaging
- Disaster-specific safety advice

### Feedback & Validation
- Trust scoring
- Duplicate detection
- Corroboration analysis

### Prediction
- Escalation probability
- Severity forecasting
- Population impact estimation
- Resource needs forecasting

---

## Performance Metrics

- Single incident processing: 2-5 seconds
- Full pipeline: 8-11 seconds
- Batch processing: Scales linearly
- Database queries: Sub-100ms

---

## Key Technologies

- **Backend**: FastAPI, Uvicorn
- **Database**: SQLite, Qdrant (optional)
- **LLM**: Ollama
- **Entity Extraction**: GLiNER
- **Orchestration**: CrewAI (optional)
- **Geocoding**: Nominatim
- **Containerization**: Docker, Docker Compose
- **Frontend**: Next.js, React
- **Testing**: PyTest

---

**Emergency Response Agent** - Intelligent Disaster Management Platform

**Version**: v1.0.0
**Status**: Production Ready
**Python Version**: 3.10+
**Node.js Version**: 18+
**Last Updated**: June 2025
