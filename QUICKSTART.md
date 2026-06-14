# QUICK START GUIDE

Get the Disaster Management Platform running in 5 minutes.

## Prerequisites

- Docker & Docker Compose installed
- Port 8000-8003, 11434 available
- 8GB RAM recommended

## Option 1: Docker Compose (Fastest)

### Start All Services

```bash
# Navigate to repository root
cd /path/to/DISASTER\ DETECTION\ AGENT

# Start all services
docker-compose -f docker-compose.full.yml up -d

# Wait for services to be ready (check logs)
docker-compose -f docker-compose.full.yml logs -f

# Health check
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/assessments/health
curl http://localhost:8002/api/v1/health
curl http://localhost:8003/api/v1/health
```

### Check Logs

```bash
# All services
docker-compose -f docker-compose.full.yml logs

# Specific service
docker-compose -f docker-compose.full.yml logs detection_agent
docker-compose -f docker-compose.full.yml logs prediction_agent
```

### Stop Services

```bash
docker-compose -f docker-compose.full.yml down
```

## Option 2: Manual Setup (Development)

### Install Dependencies

```bash
# Shared dependencies
pip install -r shared/requirements.txt

# Detection Agent
cd Detection_agent && pip install -r requirements.txt

# Assessment Agent
cd ../Assessment_agent/backend && pip install -r requirements.txt

# Disaster Agents
cd ../../ && pip install -r Disaster_agent_api/requirements.txt

# Prediction Agent
pip install -r Prediction_agent/requirements.txt
```

### Start Each Service in Separate Terminals

**Terminal 1 - Detection Agent (Port 8000)**
```bash
cd Detection_agent
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Assessment Agent (Port 8001)**
```bash
cd Assessment_agent/backend
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 3 - Disaster Agents (Port 8002)**
```bash
python -m uvicorn Disaster_agent_api.main:app --reload --port 8002
```

**Terminal 4 - Prediction Agent (Port 8003)**
```bash
cd Prediction_agent
python -m uvicorn main:app --reload --port 8003
```

**Terminal 5 - Ollama (Optional, Port 11434)**
```bash
ollama serve
```

## First Test - Submit an Incident

### Step 1: Submit Incident to Detection

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

**Expected Response** (incident detected):
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

### Step 2: Wait for Pipeline Processing (8-11 seconds)

The incident automatically triggers:
1. Assessment
2. GIS Analysis
3. Resource Allocation
4. Route Optimization
5. Communication
6. Feedback
7. Prediction

### Step 3: Check Assessment

```bash
curl http://localhost:8001/api/v1/assessments/history?limit=1
```

**Expected Response**:
```json
{
  "items": [
    {
      "incident_id": "INC-2024-001",
      "severity": "High",
      "priority": "Critical",
      "risk_score": 87,
      "resource_urgency": "Immediate",
      "escalation_required": true
    }
  ]
}
```

### Step 4: Get Prediction

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
      "infrastructure_vulnerability": "Medium",
      "resource_availability": "Medium"
    }
  }'
```

**Expected Response**:
```json
{
  "incident_id": "INC-2024-001",
  "escalation_probability": 0.75,
  "predicted_severity": "High",
  "population_impact": 7500,
  "infrastructure_impact": 0.64,
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
  "confidence": 0.80
}
```

## API Documentation

### Access Interactive API Docs

- Detection Agent: http://localhost:8000/docs
- Assessment Agent: http://localhost:8001/docs
- Disaster Agents: http://localhost:8002/docs
- Prediction Agent: http://localhost:8003/docs

### Browse API Endpoints

```bash
# Detection endpoints
GET  http://localhost:8000/api/v1/incidents/
GET  http://localhost:8000/api/v1/incidents/{incident_id}
POST http://localhost:8000/api/v1/detect/detect

# Assessment endpoints
GET  http://localhost:8001/api/v1/assessments/health
GET  http://localhost:8001/api/v1/assessments/history
POST http://localhost:8001/api/v1/assessments/assess

# Disaster agent endpoints
POST http://localhost:8002/api/v1/gis/analyze
POST http://localhost:8002/api/v1/resource/allocate
POST http://localhost:8002/api/v1/route/optimize
POST http://localhost:8002/api/v1/communication/generate-alerts
POST http://localhost:8002/api/v1/feedback/submit

# Prediction endpoints
POST http://localhost:8003/api/v1/predict
```

## Run Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Run Specific Tests

```bash
# Prediction engine tests
pytest tests/test_integration.py::test_prediction_engine_basic -v

# High escalation scenario
pytest tests/test_integration.py::test_prediction_high_escalation -v

# Low escalation scenario
pytest tests/test_integration.py::test_prediction_low_escalation -v
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # Detection
lsof -i :8001  # Assessment
lsof -i :8002  # Disaster Agents
lsof -i :8003  # Prediction

# Kill process
kill -9 <PID>
```

### Services Not Responding

```bash
# Check service health
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/assessments/health
curl http://localhost:8002/api/v1/health
curl http://localhost:8003/api/v1/health

# View logs
docker-compose -f docker-compose.full.yml logs --tail=50
```

### Database Issues

```bash
# Reset databases
rm -f *.db

# Restart services
docker-compose -f docker-compose.full.yml restart
```

### Ollama Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull model if needed
ollama pull qwen2:latest
```

## Next Steps

1. **Explore Full Documentation**: See `INTEGRATION_README.md`
2. **Understand Architecture**: Read `ARCHITECTURE.md`
3. **Review Implementation**: See `IMPLEMENTATION_SUMMARY.md`
4. **Experiment with API**: Use `/docs` endpoints
5. **Deploy to Production**: Follow deployment guide

## Common Tasks

### Submit Batch of Incidents

```bash
curl -X POST http://localhost:8000/api/v1/detect/detect/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "source_type": "news_report",
        "content": "Flood in Dehradun",
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "source_type": "social_media",
        "content": "Earthquake felt in Haridwar",
        "timestamp": "2024-01-15T10:35:00Z"
      }
    ]
  }'
```

### Generate Alerts for Incident

```bash
curl -X POST http://localhost:8002/api/v1/communication/generate-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "incident_type": "Flood",
    "location": "Dehradun",
    "latitude": 30.2,
    "longitude": 78.1,
    "affected_population": 5000,
    "severity": "High"
  }'
```

### Submit Feedback Report

```bash
curl -X POST http://localhost:8002/api/v1/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "feedback_type": "Route Blocked",
    "source_type": "NDRF Responder",
    "message": "Rajpur Road blocked by debris",
    "road": "Rajpur Rd"
  }'
```

## Getting Help

- **API Docs**: Visit http://localhost:8000/docs (and 8001, 8002, 8003)
- **Full Documentation**: See `INTEGRATION_README.md`
- **Architecture Details**: See `ARCHITECTURE.md`
- **Code Examples**: Check `tests/test_integration.py`

---

**Happy Disaster Management! 🚀**
