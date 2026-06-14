# Data Schema Reference & Integration Examples

## Detection Agent: Complete Data Flow Example

### Input: DetectionRequest
```json
{
  "source_type": "news_report",
  "source_id": "news_bbc_001",
  "content": "Devastating floods reported in Rajpur Road area of Dehradun. Water levels rising rapidly. Residents evacuation ongoing.",
  "timestamp": "2025-01-13T14:30:00Z",
  "language": "en",
  "metadata": {
    "author": "BBC India",
    "channel": "news_api",
    "location_hint": "Dehradun, India"
  },
  "sensor_data": {
    "water_level": 2.5,
    "rainfall": 45.2,
    "temperature": 22.5
  }
}
```

### Output: DetectionResponse
```json
{
  "incident_id": "INC_20250113_AB7F9E",
  "incident_type": "Flood",
  "location": "Rajpur Road, Dehradun",
  "latitude": 30.3165,
  "longitude": 78.0322,
  "affected_population": 8500,
  "casualties": 12,
  "urgency": "High",
  "confidence": 0.89,
  "source_count": 1,
  "timestamp": "2025-01-13T14:30:00Z",
  "extraction_debug": {
    "rule_hits": [
      "keyword_flood_detected",
      "location_identified_rajpur_road",
      "severity_high_water_level"
    ],
    "entities": {
      "gliner_entities": [
        {"label": "LOCATION", "text": "Rajpur Road", "score": 0.92},
        {"label": "DISASTER", "text": "floods", "score": 0.95}
      ],
      "grouped_entities": {
        "location": ["Rajpur Road", "Dehradun"],
        "disaster_types": ["flood"]
      },
      "geocoding": {
        "location": "Rajpur Road, Dehradun",
        "latitude": 30.3165,
        "longitude": 78.0322,
        "provider": "nominatim",
        "accuracy": "street"
      },
      "confidence_components": {
        "source_trustworthiness": 0.85,
        "rule_agreement": 0.92,
        "llm_confidence": 0.88,
        "historical_uniqueness": 0.95,
        "geocoding_success": 0.98
      },
      "llm_reasoning": "News report mentions devastating floods with rising water levels and ongoing evacuation. Confirms high-urgency incident.",
      "llm_source_signals": ["evacuation_mentioned", "water_level_rising"]
    },
    "model_used": "gliner-base-en + ollama + confidence_engine + nominatim"
  }
}
```

---

## Assessment Agent: Complete Evaluation Flow

### Input: IncidentInput
```json
{
  "incident_id": "INC_20250113_AB7F9E",
  "incident_type": "Flood",
  "location": "Rajpur Road, Dehradun",
  "affected_population": 8500,
  "confidence": 0.89,
  "water_level": 2.5,
  "source_count": 1,
  "timestamp": "2025-01-13T14:30:00Z"
}
```

### Processing Pipeline
```
1. SeverityEngine.assess(incident)
   → checks: incident_type, affected_population, confidence
   → applies: water_level modifier (if flood)
   → outputs: severity=High, priority=P2, resource_urgency=Urgent

2. RiskEngine.calculate(incident, severity)
   → base_risk = affected_population * 0.5 + confidence * 50
   → severity_multiplier: Critical=1.0, High=0.75, Medium=0.5, Low=0.25
   → outputs: risk_score = 75

3. ResourceEngine.recommend(incident, severity)
   → lookup base resources for Flood + High
   → applies multipliers: population_score (affects counts)
   → outputs: {ambulances: 5, rescue_teams: 4, boats: 5, fire_trucks: 0, ...}

4. EscalationEngine.should_escalate(incident, severity, risk_score)
   → escalation = (risk_score > 70 AND severity in [Critical, High]) OR (affected_population > 5000)
   → outputs: escalation_required = true

5. ExplanationService.enhance(response)
   → optional LLM call for enhanced explanation
   → outputs: "Flood at Rajpur Road classified as High severity..."
```

### Output: AssessmentResponse
```json
{
  "incident": {
    "incident_id": "INC_20250113_AB7F9E",
    "incident_type": "Flood",
    "location": "Rajpur Road, Dehradun",
    "affected_population": 8500,
    "confidence": 0.89,
    "water_level": 2.5,
    "source_count": 1,
    "timestamp": "2025-01-13T14:30:00Z"
  },
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
  },
  "explanation": "Flood at Rajpur Road, Dehradun classified as High severity with risk score 75. Large affected population (8500) and rising water level require urgent resource deployment and escalation.",
  "decision_trace": [
    "Incident type: Flood",
    "Location: Rajpur Road, Dehradun",
    "Affected population: 8500 (HIGH)",
    "Confidence: 0.89 (HIGH)",
    "Severity assigned: High",
    "Priority assigned: P2",
    "Risk score calculated: 75",
    "Resource urgency: Urgent",
    "Water level 2.5m triggers flood protocol",
    "Escalation required: YES (risk > 70 AND large population)"
  ],
  "sop_context": [
    "Flood SOP-001: Coordinate with NDRF for water rescue",
    "Flood SOP-002: Activate shelter system for 8000+ evacuees"
  ],
  "model_used": "rule-engine-v1"
}
```

---

## Disaster Agent: Multi-Step Processing

### Stage 1: GIS Analysis Input
```json
{
  "incident_id": "INC_20250113_AB7F9E",
  "incident_type": "Flood",
  "severity": "High",
  "latitude": 30.3165,
  "longitude": 78.0322,
  "location_name": "Rajpur Road, Dehradun",
  "population_density": "High",
  "infrastructure_vulnerability": "High",
  "resource_availability": "Medium",
  "environmental_condition": "High"
}
```

### Stage 1: GIS Analysis Output
```json
{
  "incident_id": "INC_20250113_AB7F9E",
  "risk_assessment": {
    "risk_level": "High",
    "probability": 0.85,
    "high_prob": 0.85,
    "medium_prob": 0.12,
    "low_prob": 0.03
  },
  "priority_zone": "CRITICAL",
  "affected_radius_km": 4.5,
  "nearby_resources": [
    {
      "name": "Doon Hospital",
      "type": "Hospital",
      "latitude": 30.3255,
      "longitude": 78.0421,
      "distance_km": 1.2
    },
    {
      "name": "NDRF Camp",
      "type": "Rescue",
      "latitude": 30.3445,
      "longitude": 77.9853,
      "distance_km": 5.1
    },
    {
      "name": "Rajpur Fire Station",
      "type": "Fire Station",
      "latitude": 30.3580,
      "longitude": 78.0680,
      "distance_km": 3.8
    }
  ],
  "map_file": "maps/map_INC_20250113_AB7F9E.html"
}
```

### Stage 2: Resource Allocation Input (using GIS output)
```json
{
  "incident_type": "Flood",
  "severity": "High",
  "risk_probability": 0.85,
  "population_density": "High",
  "resource_availability": "Medium",
  "infrastructure_vulnerability": "High",
  "affected_population": 8500,
  "deduct_from_inventory": true
}
```

### Stage 2: Resource Allocation Output
```json
{
  "priority_score": 8.9,
  "priority_level": "CRITICAL",
  "resources": {
    "ambulances": 7,
    "rescue_teams": 6,
    "boats": 6,
    "fire_trucks": 2
  },
  "actual_resources": {
    "ambulances": 7,
    "rescue_teams": 6,
    "boats": 5,
    "fire_trucks": 2
  },
  "inventory_before": {
    "ambulances": 10,
    "rescue_teams": 8,
    "boats": 6,
    "fire_trucks": 5
  },
  "inventory_after": {
    "ambulances": 3,
    "rescue_teams": 2,
    "boats": 1,
    "fire_trucks": 3
  },
  "deployment_order": ["boats", "rescue_teams", "ambulances", "fire_trucks"],
  "component_scores": {
    "risk_score": 8.5,
    "population_score": 8.5,
    "shortage_score": 5.0
  },
  "justification": "CRITICAL priority due to 85% risk probability, High population density, and High infrastructure vulnerability combined with large affected population (8500)."
}
```

### Stage 3: Route Optimization Input (for primary rescue resource)
```json
{
  "from_node": "ndrf_camp",
  "to_incident_lat": 30.3165,
  "to_incident_lon": 78.0322,
  "current_road_risks": {
    "Rajpur Rd": {
      "flood_risk": 0.80,
      "road_damage": 0.40
    },
    "Station Rd": {
      "flood_risk": 0.50,
      "road_damage": 0.20
    }
  }
}
```

### Stage 3: Route Optimization Output
```json
{
  "status": "OK",
  "from_node": "ndrf_camp",
  "to_node": "parade_ground",
  "route": ["ndrf_camp", "prem_nagar", "race_course", "parade_ground"],
  "distance_km": 5.2,
  "time_minutes": 15.3,
  "eta": "2025-01-13T14:45:18Z",
  "cost_breakdown": {
    "base_time_min": 15.3,
    "flood_penalty": 0.8,
    "damage_penalty": 0.4,
    "traffic_penalty": 1.2,
    "total_composite_cost": 17.7
  },
  "blocked_roads_active": [],
  "warning": "Rajpur Rd flooded (80% risk) - route avoids this area"
}
```

### Stage 4: Communication Alerts Output
```json
{
  "citizen_alert": "🌊 EVACUATION ORDER — FLOOD 🔴\n────────────────────────────────────────────────\n📍 Location : Rajpur Road, Dehradun\n⚡ Severity : High    Risk: High (85%)\n📍 Affected area: 4.5 km radius around Rajpur Road.\n\n⚠️ IMMEDIATE ACTION REQUIRED\n\nMove to higher ground immediately. Do not cross flooded roads.\nAvoid Rajpur Rd — use alternate routes (Haridwar Bypass available).\n\nEnglish: Move to higher ground immediately. Do not cross flooded roads.\nहिंदी: तुरंत ऊँचे स्थान पर जाएं। बाढ़ वाली सड़कों पर न जाएं।\n\nHelp: Contact 1234 for evacuation, 911 for emergency\nDate: 13 Jan 2025, 14:30\n",
  "authority_report": "High-severity flood at Rajpur Road, Dehradun. 8500 affected. Resource deployment: 7 ambulances, 6 rescue teams, 5 boats. NDRF ETA 14:45. Rajpur Rd blocked—alternate routes active. Escalation: YES. SOP-001 activated.",
  "sms_alert": "🌊EVACUATE RAJPUR RD: Move to higher ground NOW. Flooded roads—use Haridwar Bypass. Help: 1234. Official updates: emergency.in",
  "alert_tier": "EVACUATION ORDER",
  "timestamp": "2025-01-13T14:30:00Z"
}
```

### Stage 5: Feedback Loop (from responders)
```json
{
  "incident_id": "INC_20250113_AB7F9E",
  "feedback_type": "Route Blocked",
  "description": "Station Road completely submerged, impassable",
  "source": "Field Responder",
  "location": "Dehradun",
  "road": "Station Rd",
  "submission": {
    "id": 1,
    "trust_score": 0.88,
    "timestamp": "2025-01-13T14:35:00Z",
    "verified": true,
    "duplicate": false,
    "recommended_action": {
      "action": "BLOCK_ROAD",
      "road": "Station Rd",
      "trigger_reroute": true,
      "confidence": 0.88,
      "reason": "High-trust source (Field Responder) — immediate action."
    }
  },
  "consequence": {
    "action_taken": "BLOCK_ROAD",
    "route_recomputed": {
      "new_route": ["ndrf_camp", "prem_nagar", "race_course", "rest_camp", "haridwar_road", "sector_17"],
      "new_time_minutes": 18.5,
      "new_eta": "2025-01-13T14:48:30Z",
      "delay_seconds": 192
    }
  }
}
```

---

## Integration Sequence: Complete Example

```
1. USER/SYSTEM submits raw incident text via Detection API
   ↓
2. Detection Agent:
   - Extracts entities (NER)
   - Runs rule engine
   - LLM classification
   - Geocoding
   - Confidence scoring
   ↓
3. DetectionResponse stored in Detection DB
   ↓ (MANUAL CONVERSION NEEDED)
4. Convert to IncidentInput format
   ↓
5. Assessment Agent:
   - Severity assessment
   - Risk scoring
   - Resource recommendation
   - Escalation check
   ↓
6. AssessmentResponse stored in Assessment DB
   ↓ (MISSING FIELDS - REQUIRES ENHANCEMENT)
7. Add infrastructure_vulnerability, resource_availability, environmental_condition
   ↓
8. Disaster Agent (offline):
   - GIS analysis → risk_assessment + affected_radius + nearby_resources
   - Resource allocation → priority_score + actual_resources + inventory_after
   - Route optimization → fastest_route + ETA + cost_breakdown
   - Communication → bilingual alerts
   ↓
9. Responder actions trigger feedback
   ↓
10. Feedback Agent:
    - Trust scoring
    - Duplicate detection
    - Corroboration check
    - Recommendation (BLOCK_ROAD, INCREASE_RESOURCES, etc.)
    ↓
11. Actions executed locally + feedback stored in JSON
    ↓ (MISSING: FEEDBACK LOOP BACK TO ASSESSMENT/DETECTION)
12. [If integrated] Update route graph, resource inventory, system state
```

---

## Missing Integration Examples

### What Assessment needs to provide for Disaster agents:
```python
# Current AssessmentResponse
{
  "severity": "High",
  "priority": "P2",
  "risk_score": 75,
  "resource_urgency": "Urgent",
  "recommended_resources": {...},
  "escalation_required": true,
}

# What Disaster agents need additionally:
{
  "infrastructure_vulnerability": "High",  # ← MISSING
  "resource_availability": "Medium",       # ← MISSING
  "environmental_condition": "High",       # ← MISSING
  "population_density": "High",            # ← Inferred from affected_population?
  "incident_type": "Flood",                # ← Available but not in assessment
  "latitude": 30.3165,                     # ← Not in assessment (separate concern)
  "longitude": 78.0322,                    # ← Not in assessment
  "location_name": "Rajpur Road, Dehradun",# ← Available as "location"
}
```

### What Disaster feedback should loop back:
```python
# Feedback actions generated:
[
  {"action": "BLOCK_ROAD", "road": "Station Rd", "confidence": 0.88},
  {"action": "INCREASE_RESOURCES", "type": "boats", "quantity": 2},
  {"action": "REDIRECT_EVACUEES", "shelter": "Sector 17 High School"},
]

# Should update Assessment with:
{
  "road_blockages": ["Station Rd"],
  "resource_availability": "Low",  # Was Medium, now depleted
  "evacuation_route": "via_haridwar_bypass",
  "shelter_status": "Sector_17_operational",
}
```

---

## Recommended API Contract for Integration

### Detection → Assessment Bridge
```
POST /api/v1/assessments/assess-from-detection
{
  "detection_response": DetectionResponse,
  "infrastructure_data": {
    "infrastructure_vulnerability": "High" | "Medium" | "Low",
    "population_density": "High" | "Medium" | "Low",
    "resource_availability": "High" | "Medium" | "Low",
    "environmental_condition": "High" | "Medium" | "Low"
  }
}
→ AssessmentResponse
```

### Assessment → Disaster Bridge
```
POST /api/v1/disaster/process-incident
{
  "assessment_response": AssessmentResponse,
  "geo_context": {
    "latitude": float,
    "longitude": float,
    "location_name": string,
    "infrastructure_vulnerability": string,
    "resource_availability": string,
    "environmental_condition": string,
    "population_density": string
  }
}
→ {
  "gis_analysis": {...},
  "resource_plan": {...},
  "route_plan": {...},
  "alerts": {...}
}
```

### Disaster Feedback → System Update
```
POST /api/v1/system/apply-feedback
{
  "incident_id": string,
  "feedback_action": FeedbackAction,
  "consequences": {
    "blocked_roads": [string],
    "resource_deductions": {...},
    "route_changes": [...],
    "escalation_updates": {...}
  }
}
→ Updated system state
```

