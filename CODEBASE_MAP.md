# Disaster Detection Agent - Codebase Architecture Map

## Executive Summary

This disaster management system consists of three interconnected agent subsystems:
1. **Detection Agent** - Identifies and classifies incidents from multiple sources
2. **Assessment Agent** - Evaluates severity, risk, and resource requirements
3. **Disaster Agent** - Manages spatial analysis, resource allocation, routing, communication, and feedback

Current integration: **Minimal** - Detection and Assessment agents are independent. Disaster agents operate offline and are not currently integrated with the API backend.

---

## Part 1: Detection Agent (`Detection_agent/`)

### 1.1 API Endpoints

**File:** [Detection_agent/app/api/router.py](Detection_agent/app/api/router.py)  
**Base URL:** `/api/v1`  
**Routes included:**
- `/api/v1/health/` - Health checks
- `/api/v1/detect/` - Detection endpoints
- `/api/v1/social/` - Social media monitoring
- `/api/v1/incidents/` - Incident history and queries
- `/api/v1/crew/` - CrewAI-based detection (optional)

#### Detection Endpoints

**File:** [Detection_agent/app/api/routes/detection.py](Detection_agent/app/api/routes/detection.py)

| Endpoint | Method | Input Schema | Output Schema | Purpose |
|----------|--------|--------------|---------------|---------|
| `/detect/detect` | POST | `DetectionRequest` | `DetectionResponse` | Single incident detection |
| `/detect/detect/batch` | POST | `BatchDetectionRequest` | `BatchDetectionResponse` | Batch detection (multiple items) |

**CrewAI Route**

**File:** [Detection_agent/app/api/routes/crew.py](Detection_agent/app/api/routes/crew.py)

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/crew/detect` | POST | `CrewRunRequest` | JSON result from crew.kickoff() |

**Incidents Endpoints**

**File:** [Detection_agent/app/api/routes/incidents.py](Detection_agent/app/api/routes/incidents.py)

| Endpoint | Method | Query Params | Output Schema |
|----------|--------|--------------|---------------|
| `/incidents/` | GET | `incident_type`, `urgency`, `source_type`, `limit` | `IncidentListResponse` |
| `/incidents/summary` | GET | - | `IncidentSummaryResponse` |
| `/incidents/{incident_id}` | GET | - | `IncidentRead` |

---

### 1.2 Input/Output Schemas

**Location:** [Detection_agent/app/schemas/](Detection_agent/app/schemas/)

#### Input Schemas

**File:** [Detection_agent/app/schemas/request.py](Detection_agent/app/schemas/request.py)

```python
class DetectionRequest(BaseModel):
    source_type: str          # user_report | news_report | social_media | sensor_data
    source_id: Optional[str]  # Source identifier
    content: str              # Incident description (min 3 chars)
    timestamp: datetime       # When detected
    language: str = "en"
    metadata: Optional[DetectionMetadata]  # author, channel, location_hint
    sensor_data: Optional[SensorData]      # water_level, rainfall, temperature

class SensorData(BaseModel):
    water_level: Optional[float]
    rainfall: Optional[float]
    temperature: Optional[float]

class DetectionMetadata(BaseModel):
    author: Optional[str]
    channel: Optional[str]
    location_hint: Optional[str]

class BatchDetectionRequest(BaseModel):
    items: List[DetectionRequest]  # ≥ 1 item
```

#### Output Schemas

**File:** [Detection_agent/app/schemas/response.py](Detection_agent/app/schemas/response.py)

```python
class DetectionResponse(BaseModel):
    incident_id: str              # Generated UUID-like ID
    incident_type: str            # e.g., "Flood", "Earthquake"
    location: Optional[str]       # Resolved location name
    latitude: Optional[float]     # Geocoded latitude
    longitude: Optional[float]    # Geocoded longitude
    affected_population: int      # Estimated affected count
    casualties: int               # Estimated casualty count
    urgency: str                  # High | Medium | Low
    confidence: float             # 0.0-1.0, confidence in detection
    source_count: int = 1         # Number of corroborating sources
    timestamp: datetime
    extraction_debug: DetectionDebug  # Rule hits, entities, model info

class DetectionDebug(BaseModel):
    rule_hits: List[str]          # Rules triggered
    entities: Dict[str, Any]      # Extracted entities, geocoding, reasoning
    model_used: str               # Models used in pipeline

class BatchDetectionResponse(BaseModel):
    items: List[DetectionResponse]
    total: int
```

#### Incident Query Schemas

**File:** [Detection_agent/app/schemas/incident.py](Detection_agent/app/schemas/incident.py)

```python
class IncidentRead(BaseModel):
    incident_id: str
    incident_type: str
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    affected_population: int
    casualties: int
    urgency: str
    confidence: float
    source_count: int
    source_type: str
    source_id: Optional[str]
    raw_content: str
    created_at: datetime

class IncidentListResponse(BaseModel):
    items: List[IncidentRead]
    total: int

class IncidentSummaryResponse(BaseModel):
    total_incidents: int
    by_type: Dict[str, int]
    by_urgency: Dict[str, int]
```

---

### 1.3 Detection Pipeline Services

**File:** [Detection_agent/app/services/detection_pipeline.py](Detection_agent/app/services/detection_pipeline.py)

**Core Pipeline Architecture:**
```
DetectionRequest
      ↓
[1] Entity Extraction (EntityExtractor)
      ↓ → entities, NER results
[2] Rule Engine (RuleEngine)
      ↓ → rule_hits, incident_type, location, scores
[3] Incident Classifier (LLM-based via Ollama)
      ↓ → incident_type, urgency, location, reasoning
[4] History Similarity (HistoryService)
      ↓ → deduplication score
[5] Confidence Scorer (ConfidenceScorer)
      ↓ → final_confidence (weighted components)
[6] Geocoder (GeocoderService → Nominatim)
      ↓ → latitude, longitude
[7] Repository Persistence
      ↓ → Save to database
      ↓
DetectionResponse (with full extraction_debug)
```

**Service Classes:**

| Service | File | Purpose |
|---------|------|---------|
| `DetectionPipeline` | [detection_pipeline.py](Detection_agent/app/services/detection_pipeline.py) | Orchestrates all steps |
| `EntityExtractor` | [entity_extractor.py](Detection_agent/app/services/entity_extractor.py) | NER via GLiNER or fallback |
| `RuleEngine` | [rule_engine.py](Detection_agent/app/services/rule_engine.py) | Regex/keyword rules for incident type, location, urgency |
| `IncidentClassifier` | [classifier.py](Detection_agent/app/services/classifier.py) | LLM classification via Ollama (structured JSON output) |
| `ConfidenceScorer` | [confidence.py](Detection_agent/app/services/confidence.py) | Weighted scoring: source_type + rule_hits + llm_agreement + history_dedup |
| `GeocoderService` | [geocoder.py](Detection_agent/app/services/geocoder.py) | Nominatim-based geocoding with caching |
| `HistoryService` | [history.py](Detection_agent/app/services/history.py) | Similarity search via TF-IDF or embeddings |

---

### 1.4 Database Models

**File:** [Detection_agent/app/db/models.py](Detection_agent/app/db/models.py)

```python
class IncidentRecord(Base):
    __tablename__ = "incidents"
    
    id: int (primary key)
    incident_id: str (unique, indexed)
    incident_type: str (indexed)
    location: Optional[str] (indexed)
    latitude: Optional[float]
    longitude: Optional[float]
    affected_population: int
    casualties: int
    urgency: str (indexed)
    confidence: float
    source_count: int
    source_type: str (indexed)
    source_id: Optional[str] (indexed)
    raw_content: str (text blob)
    created_at: datetime (indexed, UTC)
```

**DB Setup:** [Detection_agent/app/db/base.py](Detection_agent/app/db/base.py) - SQLAlchemy DeclarativeBase  
**Session Management:** [Detection_agent/app/db/session.py](Detection_agent/app/db/session.py) - AsyncSession factory

---

### 1.5 Key Implementation Details

**Entity Extraction Strategy:**  
- Primary: GLiNER model (local, GPU-optional)
- Fallback: Rule-based extraction if GLiNER unavailable

**Rule Engine Rules:**  
- Keyword triggers for incident types (flood keywords, earthquake keywords, etc.)
- Location extraction via regex and known place names
- Severity/urgency heuristics based on keywords

**Confidence Components:**
- Source type trustworthiness (sensor_data > news > social_media > user_report)
- Rule engine agreement (number of rules triggered)
- LLM classifier agreement (cross-validation)
- Historical uniqueness (penalizes near-duplicates)
- Geocoding success

**Deployment:**
```
Docker setup: Detection_agent/Dockerfile
Entry point: Detection_agent/app/main.py
FastAPI app with CORS middleware
Health checks on startup
```

---

---

## Part 2: Assessment Agent (`Assessment_agent/backend/`)

### 2.1 API Endpoints

**File:** [Assessment_agent/backend/app/api/assessment_routes.py](Assessment_agent/backend/app/api/assessment_routes.py)  
**Base URL:** `/api/v1/assessments`

| Endpoint | Method | Input Schema | Output Schema | Purpose |
|----------|--------|--------------|---------------|---------|
| `/health` | GET | - | Health dict | Service health check |
| `/assess` | POST | `IncidentInput` | `AssessmentResponse` | Single incident assessment |
| `/assess/batch` | POST | `BatchAssessmentRequest` | `BatchAssessmentResponse` | Batch assessment |
| `/assess/upload-json` | POST | File (JSON) | `BatchAssessmentResponse` | Upload and assess JSON incidents |
| `/assess/from-file` | GET | - | `AssessmentResponse` | Demo assessment from local file |
| `/assess/from-file/{incident_id}` | GET | Path param | `AssessmentResponse` | Load specific incident by ID |
| `/history` | GET | - | `StoredAssessmentListResponse` | Get all past assessments |
| `/dashboard` | GET | - | `FrontendDashboardResponse` | Dashboard summary |
| `/geocode` | GET | `location` query param | Geocoding result dict | Nominatim geocoding service |

---

### 2.2 Input/Output Schemas

**Location:** [Assessment_agent/backend/app/schemas/](Assessment_agent/backend/app/schemas/)

#### Input Schema

**File:** [Assessment_agent/backend/app/schemas/incident.py](Assessment_agent/backend/app/schemas/incident.py)

```python
class IncidentInput(BaseModel):
    incident_id: Optional[str] = None  # Auto-generated if missing
    incident_type: str                 # Min 2, max 100 chars (title-cased)
    location: str                      # Min 2, max 200 chars
    affected_population: int           # ≥ 0
    confidence: float                  # 0.0–1.0
    water_level: Optional[float] = None
    source_count: int = 1              # ≥ 0
    timestamp: Optional[datetime] = None
```

#### Output Schemas

**File:** [Assessment_agent/backend/app/schemas/assessment.py](Assessment_agent/backend/app/schemas/assessment.py)

```python
class AssessmentResponse(BaseModel):
    incident: IncidentInput
    severity: str                      # Critical | High | Medium | Low
    priority: str                      # P1 | P2 | P3 | P4
    risk_score: int                    # 0–100
    resource_urgency: str              # Immediate | Urgent | Moderate | Low
    escalation_required: bool
    recommended_resources: RecommendedResources
    explanation: str                   # Human-readable justification
    decision_trace: List[str]          # Decision steps logged
    sop_context: List[str] = []        # Standard Operating Procedure context (from Qdrant)
    model_used: str = "rule-engine-v1"

class RecommendedResources(BaseModel):
    ambulances: int = 0
    rescue_teams: int = 0
    fire_units: int = 0
    police_units: int = 0
    medical_teams: int = 0
    shelters: int = 0

class BatchAssessmentRequest(BaseModel):
    incidents: List[IncidentInput]

class BatchAssessmentResponse(BaseModel):
    items: List[AssessmentResponse]
    total: int

class FrontendDashboardResponse(BaseModel):
    total_incidents: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    items: List[FrontendAssessmentCard]  # Severity breakdown
```

---

### 2.3 Assessment Pipeline Services

**File:** [Assessment_agent/backend/app/services/assessment_orchestrator.py](Assessment_agent/backend/app/services/assessment_orchestrator.py)

**Core Assessment Architecture:**
```
IncidentInput
      ↓
[1] Severity Engine (SeverityEngine)
      ↓ → severity (Critical/High/Medium/Low)
      ↓ → priority (P1/P2/P3/P4)
      ↓ → resource_urgency
      ↓ → reasons (list of justifications)
[2] Risk Engine (RiskEngine)
      ↓ → risk_score (0–100)
[3] Resource Recommendation Engine (ResourceEngine)
      ↓ → RecommendedResources (ambulances, rescue_teams, etc.)
[4] Escalation Engine (EscalationEngine)
      ↓ → escalation_required: bool
[5] Explanation Service (ExplanationService)
      ↓ → enhanced explanation (optional LLM)
[6] Decision Trace Builder
      ↓
AssessmentResponse
```

**Service Classes:**

| Service | File | Purpose |
|---------|------|---------|
| `AssessmentOrchestrator` | [assessment_orchestrator.py](Assessment_agent/backend/app/services/assessment_orchestrator.py) | Main orchestrator |
| `SeverityEngine` | [severity_engine.py](Assessment_agent/backend/app/services/severity_engine.py) | Rule-based severity classification |
| `RiskEngine` | [risk_engine.py](Assessment_agent/backend/app/services/risk_engine.py) | Weighted risk scoring (0–100) |
| `ResourceEngine` | [resource_engine.py](Assessment_agent/backend/app/services/resource_engine.py) | Resource allocation recommendation |
| `EscalationEngine` | [escalation_engine.py](Assessment_agent/backend/app/services/escalation_engine.py) | Escalation decision logic |
| `ExplanationService` | [explanation_service.py](Assessment_agent/backend/app/services/explanation_service.py) | LLM-enhanced explanations (optional Ollama) |
| `PersistenceService` | [persistence_service.py](Assessment_agent/backend/app/services/persistence_service.py) | DB save/load assessments and incidents |
| `DashboardService` | [dashboard_service.py](Assessment_agent/backend/app/services/dashboard_service.py) | Aggregates for frontend dashboard |
| `LLMService` (Ollama) | [llm_service.py](Assessment_agent/backend/app/services/llm_service.py) | Local LLM service wrapper |
| `QdrantService` | [qdrant_service.py](Assessment_agent/backend/app/services/qdrant_service.py) | Vector DB for SOP retrieval |
| `GeocodingService` | [geocoding_service.py](Assessment_agent/backend/app/services/geocoding_service.py) | Nominatim-based geocoding |

---

### 2.4 Database Models

**File:** [Assessment_agent/backend/app/models/](Assessment_agent/backend/app/models/)

#### IncidentRecord

**File:** [Assessment_agent/backend/app/models/incident.py](Assessment_agent/backend/app/models/incident.py)

```python
class IncidentRecord(Base):
    __tablename__ = "incidents"
    
    id: int (primary key)
    incident_id: str (unique, indexed)
    incident_type: str (indexed)
    location: str
    affected_population: int
    confidence: float
    water_level: Optional[float]
    source_count: int = 1
    timestamp: Optional[datetime]
    created_at: datetime (default: utc now)
```

#### AssessmentRecord

**File:** [Assessment_agent/backend/app/models/assessment.py](Assessment_agent/backend/app/models/assessment.py)

```python
class AssessmentRecord(Base):
    __tablename__ = "assessments"
    
    id: int (primary key)
    incident_id: str (indexed)
    severity: str                    # Critical | High | Medium | Low
    priority: str                    # P1–P4
    risk_score: int                  # 0–100
    resource_urgency: str            # Immediate | Urgent | Moderate | Low
    escalation_required: bool
    explanation: str (text)
    recommended_resources_json: str  # JSON blob
    decision_trace_json: str         # JSON blob
    model_used: str = "rule-engine-v1"
    created_at: datetime
```

---

### 2.5 CrewAI Integration (Optional)

**File:** [Assessment_agent/backend/app/agents/crew_setup.py](Assessment_agent/backend/app/agents/crew_setup.py)

**Optional review crew for assessments:**
- Agents: AssessmentReviewer, ResourceReviewer, OperationsSummaryWriter
- Tasks: Review incident context, validate resource recommendations, write summary
- Input: incident_payload dict + assessment_payload dict
- Output: crew_summary (text)

This is **NOT** currently integrated with the API endpoints but available for enhancement.

---

---

## Part 3: Disaster Agent (`Disaster/`)

### 3.1 Agent Architecture

The Disaster Agent operates **offline** and orchestrates five specialized agents for comprehensive incident response.

**Test Pipeline:** [Disaster/Testpipeline.py](Disaster/Testpipeline.py)  
**Agents Directory:** [Disaster/agents/](Disaster/agents/)

---

### 3.2 GIS Agent

**File:** [Disaster/agents/gis_agent.py](Disaster/agents/gis_agent.py)

**Purpose:** Spatial analysis, risk assessment, affected area mapping

**Input Schema:**
```python
incident = {
    'incident_id':                'INC001',
    'incident_type':              'Flood' | 'Earthquake' | 'Tsunami' | 'Cyclone' | 'Landslide' | 'Fire',
    'severity':                   'High' | 'Medium' | 'Low',
    'latitude':                   float,
    'longitude':                  float,
    'location_name':              str,
    'population_density':         'High' | 'Medium' | 'Low',
    'infrastructure_vulnerability': 'High' | 'Medium' | 'Low',
    'resource_availability':      'High' | 'Medium' | 'Low',
    'environmental_condition':    'High' | 'Medium' | 'Low',
}
```

**Output Schema:**
```python
{
    'incident_id':         str,
    'incident':            dict (input copy),
    'risk_assessment': {
        'risk_level':      'High' | 'Medium' | 'Low',
        'probability':     float (0–1, P(Risk=High)),
        'high_prob':       float,
        'medium_prob':     float,
        'low_prob':        float,
    },
    'priority_zone':       'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW',
    'affected_radius_km':  float,
    'nearby_resources': [
        {
            'name':        str,
            'type':        'Hospital' | 'Fire Station' | 'Police Station' | 'Shelter',
            'latitude':    float,
            'longitude':   float,
            'distance_km': float,
        },
        ...
    ],
    'map':                 folium.Map (HTML saved to maps/map_{incident_id}.html),
}
```

**Core Components:**

| Component | Purpose |
|-----------|---------|
| `SimplifiedBayesianRiskAssessor` | CPT-based (Conditional Probability Table) risk calculation |
| `_CPT` dict | 27 tuples: (hazard_severity, pop_density, infra_vuln) → P(Risk=High) |
| `_DISASTER_MOD` | Disaster-type multipliers (Flood: 1.20, Earthquake: 1.00, etc.) |
| `_RESOURCE_MOD`, `_ENV_MOD` | Modifiers for resource availability and environmental conditions |
| Base radius lookup | Incident-type × severity → km coverage (dynamic scaled by risk_prob) |
| Folium mapping | Visual map with zones (red=CRITICAL, orange=HIGH, etc.) and resources |

**Key Methods:**
- `infer()` → Risk assessment dict with probabilities
- `analyze()` → Full GIS analysis including map generation
- `_affected_radius()` → Dynamic radius = base × f(risk_probability)

---

### 3.3 Resource Allocation Agent

**File:** [Disaster/agents/resource_agent.py](Disaster/agents/resource_agent.py)

**Purpose:** Determine priority score and recommend resource deployment

**Input Schema:**
```python
{
    'incident_type':                  str (Flood, Earthquake, etc.),
    'severity':                       'High' | 'Medium' | 'Low',
    'risk_probability':               float (0–1, from GIS Agent),
    'population_density':             'High' | 'Medium' | 'Low',
    'resource_availability':          'High' | 'Medium' | 'Low',
    'infrastructure_vulnerability':   'High' | 'Medium' | 'Low' (multiplier only),
    'affected_population':            int (optional, explicit count),
    'deduct_from_inventory':          bool (whether to reduce available inventory),
}
```

**Output Schema:**
```python
{
    'priority_score':     float (0–10),
    'priority_level':     'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW',
    'resources': {
        'ambulances':     int,
        'rescue_teams':   int,
        'boats':          int,
        'fire_trucks':    int,
    },
    'actual_resources': { ... },  # Constrained by inventory
    'inventory_before':   dict,
    'inventory_after':    dict,   # Updated after allocation
    'deployment_order':   List[str],
    'component_scores': {
        'risk_score':     float,
        'population_score': float,
        'shortage_score': float,
    },
    'justification':      str,
}
```

**Priority Score Formula:**
```
score = 0.60 × (risk_probability × 10)
      + 0.25 × population_score
      + 0.15 × shortage_score
```

**Resource Tables:**
- Hardcoded base resources per disaster_type + severity combination
- Multiplied by: score_multiplier (1.0 if score < 5.0, 1.25 if 5.0–7.5, 1.50 if ≥ 7.5)
- Further multiplied by: infrastructure_vulnerability (High: 1.30, Medium: 1.00, Low: 0.85)
- Capped by: available inventory

**Default Inventory:**
```python
{
    'ambulances':   10,
    'rescue_teams': 8,
    'boats':        6,
    'fire_trucks':  5,
}
```

---

### 3.4 Route Optimization Agent

**File:** [Disaster/agents/route_agent.py](Disaster/agents/route_agent.py)

**Purpose:** A* path planning with dynamic risk incorporation

**Graph Structure:**
- 17 key nodes (hospitals, police stations, incident hot zones in Dehradun area)
- 20+ edges (roads, highways, residential streets)
- Edge attributes: distance_km, time_minutes, road_type, flood_risk, road_damage, traffic_factor

**Input Schema:**

```python
# Simple route
{
    'from_node':  str,  # Hospital name, NDRF camp, etc.
    'to_node':    str,
}

# Or with incident location (auto-snap to nearest node)
{
    'from_node':  str,
    'incident_lat': float,
    'incident_lon': float,
}

# Update road risks from GIS
{
    'Rajpur Rd': {
        'flood_risk': 0.8,
        'road_damage': 0.4,
    },
    ...
}

# Find best among multiple resources
{
    'resource_nodes': [str, str, ...],  # Starting points
    'target_node': str,
}
```

**Output Schema:**
```python
{
    'status':             'OK' | 'ERROR',
    'from_node':          str,
    'to_node':            str,
    'route':              List[str],  # Ordered node sequence
    'distance_km':        float,
    'time_minutes':       float,
    'eta':                datetime (start_time + time_minutes),
    'cost_breakdown': {
        'base_time_min':  float,
        'flood_penalty':  float,
        'damage_penalty': float,
        'traffic_penalty': float,
    },
    'blocked_roads_active': List[str],
    'blocked_roads_reason': dict,
}
```

**Cost Formula:**
```
composite_cost = time_minutes × traffic_factor × (1 + flood_risk×3 + road_damage×2)
```

**Key Methods:**
- `find_route()` → A* algorithm with time-based heuristic
- `route_to_incident()` → Snap incident coordinates to nearest node, then route
- `find_best_resource_route()` → Try multiple source resources, return fastest
- `update_road_risks()` → Receive GIS flood/damage data
- `block_road_by_name()`, `unblock_road_by_name()` → Feedback integration
- `decay_road_risks()` → Time-decay on road hazards

**Key Nodes (Dehradun Test Area):**
- `doon_hospital`, `coronation_hospital`, `max_hospital` (Medical)
- `ndrf_camp`, `prem_nagar` (Rescue)
- `parade_ground`, `railway_station`, `clock_tower` (Control centers)
- `sector_17`, `haridwar_road` (Residential/hubs)

---

### 3.5 Communication Agent

**File:** [Disaster/agents/communication_agent.py](Disaster/agents/communication_agent.py)

**Purpose:** Generate bilingual emergency alerts and operational reports

**Input Schema:**
```python
{
    'incident': {
        'incident_type':      str,
        'severity':           'High' | 'Medium' | 'Low',
        'location_name':      str,
        'affected_radius_km': float,
    },
    'risk': {
        'risk_level':         'High' | 'Medium' | 'Low',
        'probability':        float (0–1),
    },
    'allocation': {
        'resources':          dict,
        'priority_level':     str,
    },
    'route': {  # Optional
        'blocked_roads_active': List[str],
        'status':             'OK' | 'ERROR',
    }
}
```

**Output Schema:**
```python
{
    'citizen_alert':      str (English + Hindi, 2–3 paragraphs),
    'authority_report':   str (Structured ops report),
    'sms_alert':          str (≤160 characters, mobile broadcast),
    'alert_tier':         'EVACUATION ORDER' | 'WARNING' | 'ADVISORY',
    'timestamp':          str (ISO 8601),
}
```

**Alert Tiers:**
- **EVACUATION ORDER** (High risk) → Immediate action required
- **WARNING** (Medium risk) → Heightened alert
- **ADVISORY** (Low risk) → Information only

**Bilingual Support:**
- English + Hindi for citizen alerts
- Emoji indicators (🌊 Flood, 🌍 Earthquake, 🔥 Fire, etc.)

**Optional LLM Enhancement:**
- If Gemini API key provided → Use LLM for advanced alert customization
- Fallback to templates if LLM unavailable

---

### 3.6 Feedback Agent

**File:** [Disaster/agents/feedback_agent.py](Disaster/agents/feedback_agent.py)

**Purpose:** Collect, validate, and action field responder feedback

**Feedback Types:**
```python
[
    'Route Blocked', 'Route Clear', 'Rescue Completed',
    'New Hazard Spotted', 'False Alarm', 'Resource Arrived',
    'Resource Delayed', 'Casualties Reported', 'Shelter Full', 'Other'
]
```

**Input Schema:**
```python
{
    'incident_id':  str,
    'feedback_type': str,  # One of above
    'description':  str,
    'source':       str,   # Control Room, NDRF, Police, Citizen, Social Media, etc.
    'location':     Optional[str],
    'road':         Optional[str],
}
```

**Output Schema:**
```python
{
    'id':                 int,
    'incident_id':        str,
    'type':               str (normalized),
    'description':        str,
    'source':             str,
    'trust_score':        float (0–1),
    'location':           Optional[str],
    'road':               Optional[str],
    'timestamp':          str,
    'unix_time':          float,
    'verified':           bool (trust ≥ 0.80),
    'duplicate':          bool,
    'recommended_action': {
        'action':         'BLOCK_ROAD' | 'UNBLOCK_ROAD' | 'INCREASE_RESOURCES' |
                          'MARK_RESOLVED' | 'REVIEW_INCIDENT' | 'CREATE_NEW_INCIDENT' |
                          'REDIRECT_EVACUEES' | 'LOG_ONLY' | 'MARK_PENDING',
        'confidence':     float,
        'reason':         str,
        'road':           Optional[str],  # For BLOCK_ROAD/UNBLOCK_ROAD
        'trigger_reroute': bool,
    }
}
```

**Trust Scoring:**
```python
TRUST_SCORES = {
    'Control Room':    0.95,
    'NDRF Responder':  0.93,
    'Field Responder': 0.88,
    'Police Officer':  0.85,
    'Fire Officer':    0.85,
    'Citizen':         0.55,
    'Social Media':    0.35,
    'Unknown':         0.30,
}
```

**Action Logic:**
1. **High-trust sources (≥0.80)** → Auto-approve action
2. **Medium-trust sources** → Require corroboration (2+ reports from different sources)
3. **Low-trust sources** → Mark pending or request more evidence
4. **Duplicates** → Suppress (same incident + type + road within 10 min window)

**Deduplication:**
- Window: 600 seconds (10 minutes)
- Criteria: same incident_id + feedback_type + road

---

### 3.7 Data Models & Storage

**File:** [Disaster/data/](Disaster/data/)

#### Resources File
**File:** [Disaster/data/resources.json](Disaster/data/resources.json)

```json
{
  "Hospital": [
    {"name": "Doon Hospital", "latitude": 30.3255, "longitude": 78.0421, ...},
    {"name": "Coronation Hospital", "latitude": 30.3162, "longitude": 78.0322, ...},
    ...
  ],
  "Fire Station": [...],
  "Police Station": [...],
  "Shelter": [...]
}
```

#### Feedback Storage
**File:** [Disaster/data/feedback.json](Disaster/data/feedback.json)

Append-only log of all feedback entries with actions taken.

---

---

## Part 4: Integration Status & Data Flow

### 4.1 Current Integration Points (Minimal)

```
┌─────────────────┐
│ Detection Agent │
│   (FastAPI)     │
│  /api/v1/detect │
└────────┬────────┘
         │
         │ DetectionResponse
         │ (incident data + confidence)
         │
         └─────────────────────┐
                               │
                               ↓ (Currently MANUAL/OFFLINE)
┌─────────────────────────────────────────────────────────┐
│        Assessment Agent (FastAPI)                       │
│  /api/v1/assessments/assess                             │
│  Input: IncidentInput (manual conversion required)      │
│  Output: AssessmentResponse                             │
│  - Severity, priority, risk score, resources            │
│  - Escalation, explanation                              │
└──────────────────────────┬────────────────────────────────┘
                           │
                           │ AssessmentResponse
                           │ (stored in DB)
                           │
                           ↓ (NO CURRENT LINK)
┌──────────────────────────────────────────────────────────┐
│         Disaster Agent (Offline Python)                 │
│  - GIS Analysis                                         │
│  - Resource Allocation                                 │
│  - Route Optimization                                  │
│  - Communication                                       │
│  - Feedback Collection                                 │
└─────────────────────────────────────────────────────────┘
```

**Current Workflow:**
1. Detection Agent detects incident → Stores in DB
2. Manual conversion: `DetectionResponse` → `IncidentInput`
3. Assessment Agent evaluates → Stores assessment in DB
4. Disaster agents **run offline** with hardcoded test incident data

**Missing Connections:**
- No API endpoint from Assessment to Disaster agents
- No feedback loop from Disaster agents back to Assessment/Detection
- Disaster agents cannot query Detection/Assessment databases
- No unified incident tracking across systems

---

### 4.2 Proposed Integration Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   Unified Event Bus / API                         │
│  (Could be Kafka, Redis, or unified REST API gateway)             │
└──────────────────────────────────────────────────────────────────┘
           ↑                    ↑                    ↑
           │                    │                    │
    [Detection]          [Assessment]          [Disaster]
    (subscribes to        (subscribes to        (subscribes to
     new incidents)      assessments)           feedback/commands)
           │                    │                    │
      Emits                Emits               Emits
      DetectionResponse    AssessmentResponse  FeedbackAction
           │                    │                    │
           ↓                    ↓                    ↓
    ┌──────────────────────────────────────────────────────┐
    │        Unified State Store (PostgreSQL)             │
    │  - incidents, assessments, feedback, routes         │
    │  - Real-time dashboard queries                      │
    └──────────────────────────────────────────────────────┘
```

---

---

## Part 5: File Reference Index

### Detection Agent

**Core:**
- [app/main.py](Detection_agent/app/main.py) - FastAPI app initialization
- [app/api/router.py](Detection_agent/app/api/router.py) - API router
- [app/api/routes/detection.py](Detection_agent/app/api/routes/detection.py) - Detection endpoints
- [app/api/routes/crew.py](Detection_agent/app/api/routes/crew.py) - CrewAI endpoints
- [app/api/routes/incidents.py](Detection_agent/app/api/routes/incidents.py) - Incident history

**Schemas:**
- [app/schemas/request.py](Detection_agent/app/schemas/request.py) - Input schemas
- [app/schemas/response.py](Detection_agent/app/schemas/response.py) - Output schemas
- [app/schemas/incident.py](Detection_agent/app/schemas/incident.py) - Incident schemas
- [app/schemas/social.py](Detection_agent/app/schemas/social.py) - Social media schemas
- [app/schemas/internal.py](Detection_agent/app/schemas/internal.py) - Internal schemas

**Services:**
- [app/services/detection_pipeline.py](Detection_agent/app/services/detection_pipeline.py) - Main pipeline
- [app/services/rule_engine.py](Detection_agent/app/services/rule_engine.py) - Rules
- [app/services/classifier.py](Detection_agent/app/services/classifier.py) - LLM classifier
- [app/services/entity_extractor.py](Detection_agent/app/services/entity_extractor.py) - NER
- [app/services/confidence.py](Detection_agent/app/services/confidence.py) - Confidence scoring
- [app/services/geocoder.py](Detection_agent/app/services/geocoder.py) - Geocoding
- [app/services/history.py](Detection_agent/app/services/history.py) - History/dedup
- [app/services/social_monitor.py](Detection_agent/app/services/social_monitor.py) - Social monitoring
- [app/services/deduplicator.py](Detection_agent/app/services/deduplicator.py) - Deduplication

**Database:**
- [app/db/base.py](Detection_agent/app/db/base.py) - SQLAlchemy base
- [app/db/models.py](Detection_agent/app/db/models.py) - IncidentRecord
- [app/db/session.py](Detection_agent/app/db/session.py) - Session management
- [app/db/init_db.py](Detection_agent/app/db/init_db.py) - DB initialization

**Config:**
- [app/core/config.py](Detection_agent/app/core/config.py) - Settings
- [app/core/startup_checks.py](Detection_agent/app/core/startup_checks.py) - Startup validation

---

### Assessment Agent

**Core:**
- [backend/app/main.py](Assessment_agent/backend/app/main.py) - FastAPI app
- [backend/app/api/assessment_routes.py](Assessment_agent/backend/app/api/assessment_routes.py) - Routes

**Schemas:**
- [backend/app/schemas/incident.py](Assessment_agent/backend/app/schemas/incident.py) - IncidentInput
- [backend/app/schemas/assessment.py](Assessment_agent/backend/app/schemas/assessment.py) - Assessment schemas

**Services:**
- [backend/app/services/assessment_orchestrator.py](Assessment_agent/backend/app/services/assessment_orchestrator.py) - Main orchestrator
- [backend/app/services/severity_engine.py](Assessment_agent/backend/app/services/severity_engine.py) - Severity
- [backend/app/services/risk_engine.py](Assessment_agent/backend/app/services/risk_engine.py) - Risk
- [backend/app/services/resource_engine.py](Assessment_agent/backend/app/services/resource_engine.py) - Resources
- [backend/app/services/escalation_engine.py](Assessment_agent/backend/app/services/escalation_engine.py) - Escalation
- [backend/app/services/explanation_service.py](Assessment_agent/backend/app/services/explanation_service.py) - Explanation
- [backend/app/services/persistence_service.py](Assessment_agent/backend/app/services/persistence_service.py) - DB persistence
- [backend/app/services/dashboard_service.py](Assessment_agent/backend/app/services/dashboard_service.py) - Dashboard
- [backend/app/services/upload_service.py](Assessment_agent/backend/app/services/upload_service.py) - File upload
- [backend/app/services/detection_source.py](Assessment_agent/backend/app/services/detection_source.py) - Detection loading
- [backend/app/services/geocoding_service.py](Assessment_agent/backend/app/services/geocoding_service.py) - Geocoding
- [backend/app/services/llm_service.py](Assessment_agent/backend/app/services/llm_service.py) - Ollama wrapper
- [backend/app/services/qdrant_service.py](Assessment_agent/backend/app/services/qdrant_service.py) - Vector DB

**Models:**
- [backend/app/models/incident.py](Assessment_agent/backend/app/models/incident.py) - IncidentRecord
- [backend/app/models/assessment.py](Assessment_agent/backend/app/models/assessment.py) - AssessmentRecord

**Agents:**
- [backend/app/agents/crew_setup.py](Assessment_agent/backend/app/agents/crew_setup.py) - CrewAI setup (optional)

**Database:**
- [backend/app/db/base.py](Assessment_agent/backend/app/db/base.py) - SQLAlchemy base
- [backend/app/db/session.py](Assessment_agent/backend/app/db/session.py) - Session
- [backend/app/db/init_db.py](Assessment_agent/backend/app/db/init_db.py) - Initialization

---

### Disaster Agent

**Agents:**
- [Disaster/agents/gis_agent.py](Disaster/agents/gis_agent.py) - GIS analysis
- [Disaster/agents/resource_agent.py](Disaster/agents/resource_agent.py) - Resource allocation
- [Disaster/agents/route_agent.py](Disaster/agents/route_agent.py) - Route optimization
- [Disaster/agents/communication_agent.py](Disaster/agents/communication_agent.py) - Alerts
- [Disaster/agents/feedback_agent.py](Disaster/agents/feedback_agent.py) - Feedback collection

**Test:**
- [Disaster/Testpipeline.py](Disaster/Testpipeline.py) - End-to-end test

**Data:**
- [Disaster/data/resources.json](Disaster/data/resources.json) - Resource registry
- [Disaster/data/feedback.json](Disaster/data/feedback.json) - Feedback log

---

---

## Part 6: Key Dependencies & Configuration

### Detection Agent

**Key Dependencies:**
```
fastapi, uvicorn          # Web framework
sqlalchemy, asyncpg       # Async database
pydantic                  # Data validation
gliner                    # NER model
ollama                    # Local LLM (optional)
geopy, nominatim          # Geocoding
crewai                    # Agent orchestration (optional)
```

**Config File:** [Detection_agent/requirements.txt](Detection_agent/requirements.txt)

---

### Assessment Agent

**Key Dependencies:**
```
fastapi, uvicorn          # Web framework
sqlalchemy                # ORM (sync, not async here)
pydantic                  # Validation
ollama                    # Local LLM
qdrant-client             # Vector DB (optional)
crewai                    # Crew orchestration (optional)
geopy, nominatim          # Geocoding
```

**Config File:** [Assessment_agent/backend/requirements.txt](Assessment_agent/backend/requirements.txt)

---

### Disaster Agent

**Key Dependencies:**
```
networkx                  # Graph algorithms (routing)
folium                    # Web maps
geopy                     # Distance calculations
google-generativeai       # Gemini LLM (optional, for comms)
```

**No FastAPI server** - runs as offline Python module.

---

---

## Part 7: Data Format Transformations

### Detection → Assessment

**Current Manual Conversion:**
```python
# DetectionResponse (from Detection Agent)
detection_result = {
    'incident_id': 'INC_20250101_ABC123',
    'incident_type': 'Flood',
    'location': 'Rajpur Road, Dehradun',
    'latitude': 30.3165,
    'longitude': 78.0322,
    'affected_population': 8000,
    'casualties': 45,
    'urgency': 'High',
    'confidence': 0.87,
    'source_count': 3,
    'timestamp': datetime(...),
    'extraction_debug': {...},
}

# Convert to IncidentInput (for Assessment Agent)
assessment_input = IncidentInput(
    incident_id=detection_result['incident_id'],
    incident_type=detection_result['incident_type'],
    location=detection_result['location'],
    affected_population=detection_result['affected_population'],
    confidence=detection_result['confidence'],
    water_level=None,  # Not available from Detection
    source_count=detection_result['source_count'],
    timestamp=detection_result['timestamp'],
)
```

**Challenges:**
- `affected_population` type match (int vs detection calc)
- Water level not available from Detection agent
- Geographic precision may differ

---

### Assessment → Disaster Agents

**Current (None) - Should be:**
```python
# AssessmentResponse (from Assessment Agent)
assessment = {
    'severity': 'High',
    'priority': 'P2',
    'risk_score': 78,
    'resource_urgency': 'Urgent',
    'recommended_resources': {
        'ambulances': 5,
        'rescue_teams': 4,
        ...
    },
}

# Prepare for Disaster Agent (GIS, Resource, etc.)
disaster_input = {
    'incident_id': incident_id,
    'incident_type': 'Flood',
    'severity': assessment['severity'],  # High → severity param
    'latitude': lat,
    'longitude': lon,
    'location_name': location,
    'population_density': 'High',  # Inferred from affected_population?
    'infrastructure_vulnerability': 'High',  # Not in assessment output!
    'resource_availability': 'Medium',  # Not in assessment output!
    'environmental_condition': 'High',  # Not in assessment output!
}
```

**Missing mappings:**
- `infrastructure_vulnerability` ← Not provided by Assessment agent
- `resource_availability` ← Not provided by Assessment agent
- `environmental_condition` ← Not provided by Assessment agent
- `population_density` ← Not directly in assessment; must infer from affected_population + location

---

---

## Part 8: Known Limitations & Integration Gaps

### 1. **No Unified API Gateway**
   - Three separate FastAPI servers (Detection, Assessment, optional Disaster)
   - Manual data conversion required between agents
   - No real-time event streaming

### 2. **Disaster Agents Offline**
   - Run as standalone Python scripts
   - Cannot query Detection/Assessment databases
   - No REST API endpoints for Disaster services
   - Feedback from Disaster agents not integrated back

### 3. **Missing Input Fields**
   - Assessment output lacks `infrastructure_vulnerability`, `resource_availability`, `environmental_condition`
   - Disaster agents require these fields but Assessment cannot provide them
   - Would require Detection agent to extract infrastructure data

### 4. **No Unified Incident Tracking**
   - Each agent maintains separate databases
   - `incident_id` passed between systems but no foreign key constraints
   - No master incident table linking all assessments and feedback

### 5. **Geocoding Duplication**
   - Detection agent geocodes → stores in response
   - Assessment agent can re-geocode if needed
   - Disaster agents recompute from lat/lon
   - No shared geocoding cache

### 6. **LLM Dependency**
   - Detection & Assessment: Optional Ollama for classification/explanation
   - Communication agent: Optional Gemini for advanced alerts
   - Templates available as fallback but produce lower-quality output

### 7. **No Persistent State Across Agents**
   - Disaster feedback actions (e.g., "BLOCK_ROAD") stored locally in JSON
   - Route blockages not reflected in Detection/Assessment systems
   - Resource inventory deductions not visible to Assessment engine

---

---

## Summary Table: Component Mapping

| Component | Location | Type | Input | Output | DB Model |
|-----------|----------|------|-------|--------|----------|
| **Detection** | Detection_agent/ | FastAPI | Raw text/sensor | DetectionResponse | IncidentRecord |
| **Assessment** | Assessment_agent/backend/ | FastAPI | IncidentInput | AssessmentResponse | IncidentRecord + AssessmentRecord |
| **GIS** | Disaster/agents/ | Python class | Incident dict | Risk assessment + map | None (in-memory) |
| **Resource** | Disaster/agents/ | Python class | Incident + GIS | Allocation plan | Inventory JSON |
| **Route** | Disaster/agents/ | Python class | Start node + risks | Route with ETA | Graph (in-memory) |
| **Communication** | Disaster/agents/ | Python class | Incident + all agents | Bilingual alerts | feedback.json |
| **Feedback** | Disaster/agents/ | Python class | Report + source | Action recommendation | feedback.json |

---

**Document Generated:** 2025-01-13  
**Last Updated:** Comprehensive mapping of Disaster Detection Agent architecture
