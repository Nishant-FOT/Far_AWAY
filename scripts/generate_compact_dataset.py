import json
import random
import math

# Define structural bounds
INCIDENT_TYPES = ["Flood", "Fire", "Earthquake", "Building Collapse", "Chemical Leak"]
LOCATIONS = ["Sector 29", "Downtown CBD", "Industrial Zone A", "Suburban Grid 4", "Highway 42"]

def calculate_synthetic_truth(i_type, pop, metric, conf):
    # Base heuristic logic for ground truth labeling
    risk_base = (pop / 20000.0) * 50 + (metric / 10.0) * 40
    risk = min(100, int(risk_base * conf))
    
    # Stratification logic
    if risk > 80: sev, pri, urg = "Critical", "Red", "Immediate"
    elif risk > 50: sev, pri, urg = "Severe", "Orange", "Immediate"
    elif risk > 25: sev, pri, urg = "Moderate", "Yellow", "Elevated"
    else: sev, pri, urg = "Low", "Green", "Routine"
    
    # Resource scaling logic based on type and severity
    amb = max(1, math.ceil(pop / 1500))
    res = max(1, math.ceil(pop / 3000)) if sev in ["Severe", "Critical"] else 0
    
    resources = {"ambulances": amb}
    if res > 0: resources["rescue_teams"] = res
    if i_type == "Chemical Leak": resources["hazmat_units"] = max(1, math.ceil(metric/3))
    if i_type == "Earthquake" and sev == "Critical": resources["heavy_machinery"] = 3
    
    return sev, pri, risk, urg, resources

def generate_dataset(num_records=1000):
    dataset = []
    for _ in range(num_records):
        i_type = random.choice(INCIDENT_TYPES)
        loc = random.choice(LOCATIONS)
        pop = random.randint(100, 25000)
        metric = round(random.uniform(1.0, 9.9), 1)
        conf = round(random.uniform(0.65, 0.99), 2)
        
        sev, pri, risk, urg, resources = calculate_synthetic_truth(i_type, pop, metric, conf)
        
        user_msg = json.dumps({"type": i_type, "loc": loc, "pop": pop, "metric": metric, "conf": conf}, separators=(',', ':'))
        asst_msg = json.dumps({"severity": sev, "priority": pri, "risk": risk, "urgency": urg, "resources": resources}, separators=(',', ':'))
        
        dataset.append({
            "messages": [
                {"role": "system", "content": "Disaster Agent. Output valid JSON only."},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": asst_msg}
            ]
        })
    return dataset

# Execute and save as JSONL for Unsloth
records = generate_dataset()
with open("disaster_compact_train.jsonl", "w") as f:
    for record in records:
        f.write(json.dumps(record) + "\n")
print("Generated 1,000 synthetic training records.")