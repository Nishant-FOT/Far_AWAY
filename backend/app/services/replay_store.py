import os
import sqlite3
import json
from typing import List, Dict, Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
DB_PATH = os.path.join(ROOT, 'backend', 'replay_store.db')


def init_db():
    # Ensure parent directory exists (containers may run with different cwd)
    parent = os.path.dirname(DB_PATH)
    try:
        os.makedirs(parent, exist_ok=True)
    except Exception:
        pass

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS replays (incident_id TEXT PRIMARY KEY, stages TEXT)'
        )
        conn.commit()
    finally:
        conn.close()


def save_stages(incident_id: str, stages: List[Dict[str, Any]]):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute('REPLACE INTO replays (incident_id, stages) VALUES (?, ?)', (incident_id, json.dumps(stages)))
        conn.commit()
    finally:
        conn.close()


def get_stages(incident_id: str) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute('SELECT stages FROM replays WHERE incident_id = ?', (incident_id,))
        row = cur.fetchone()
        if not row:
            return []
        return json.loads(row[0])
    finally:
        conn.close()


def load_all() -> Dict[str, List[Dict[str, Any]]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute('SELECT incident_id, stages FROM replays')
        out = {}
        for incident_id, stages in cur.fetchall():
            try:
                out[incident_id] = json.loads(stages)
            except Exception:
                out[incident_id] = []
        return out
    finally:
        conn.close()
