import os
import sqlite3
import json
from datetime import datetime, timedelta

# Compute DB path (matches replay_store.py logic)
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(SCRIPT_DIR, 'replay_store.db')

print('DB_PATH ->', DB_PATH)

# Sample replay: delhi_flood_001
incident_id = 'delhi_flood_001'
start = datetime.utcnow()

# Create simple timeseries: 12 timesteps with lat/lon and severity
stages = []
for i in range(12):
    ts = (start + timedelta(seconds=i * 10)).isoformat() + 'Z'
    stages.append({
        'ts': ts,
        'location': {'lat': 28.7041 + i * 0.001, 'lng': 77.1025 + i * 0.001},
        'severity': min(1.0, 0.1 * (i+1)),
        'notes': f'Sample step {i+1}'
    })

# Ensure parent directory exists
parent = os.path.dirname(DB_PATH)
os.makedirs(parent, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
try:
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS replays (incident_id TEXT PRIMARY KEY, stages TEXT)')
    cur.execute('REPLACE INTO replays (incident_id, stages) VALUES (?, ?)', (incident_id, json.dumps(stages)))
    conn.commit()
    print('Wrote replay for', incident_id)
finally:
    conn.close()

# Print out saved row
conn = sqlite3.connect(DB_PATH)
try:
    cur = conn.cursor()
    cur.execute('SELECT incident_id, stages FROM replays WHERE incident_id = ?', (incident_id,))
    row = cur.fetchone()
    if row:
        print('Verified saved replay:', row[0], 'len(stages)=', len(json.loads(row[1])))
    else:
        print('Failed to verify replay')
finally:
    conn.close()
