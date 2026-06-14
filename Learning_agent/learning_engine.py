import json
import sqlite3
import hashlib
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception:
    QdrantClient = None

logger = logging.getLogger(__name__)


class LearningRequest(BaseModel):
    incident_id: str
    incident_type: Optional[str] = None
    incident_state: Dict[str, Any]


class LearningResponse(BaseModel):
    incident_id: str
    status: str
    patterns: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    persisted_id: Optional[int] = None


def _generate_vector(text: str, dim: int = 64) -> List[float]:
    """Deterministic, lightweight vector generator for indexing.
    (Placeholder — replace with model embeddings for production.)
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vec: List[float] = []
    for i in range(dim):
        vec.append(((h[i % len(h)] & 0xFF) / 255.0))
    return vec


def _persist_sqlite(incident_id: str, payload: Dict[str, Any]) -> int:
    conn = sqlite3.connect("learning_agent.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            payload TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        "INSERT INTO learning_records (incident_id, payload) VALUES (?, ?)",
        (incident_id, json.dumps(payload)),
    )
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def _index_qdrant(incident_id: str, text: str, vector: List[float]) -> bool:
    if QdrantClient is None:
        logger.info("Qdrant client not installed; skipping indexing")
        return False

    try:
        client = QdrantClient(url="http://qdrant:6333")
        collection_name = "learning"
        # Create collection if not exists
        try:
            client.get_collection(collection_name=collection_name)
        except Exception:
            client.recreate_collection(
                collection_name=collection_name,
                vector_size=len(vector),
                distance=qmodels.Distance.COSINE,
            )

        point = qmodels.PointStruct(
            id=incident_id,
            vector=vector,
            payload={"text": text, "incident_id": incident_id},
        )
        client.upsert(collection_name=collection_name, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Qdrant indexing failed: {e}")
        return False


def analyze_and_store(request: LearningRequest) -> LearningResponse:
    # Basic pattern discovery stub (replace with real analytics)
    incident_id = request.incident_id
    payload = request.incident_state

    # Persist to SQLite
    persisted_id = _persist_sqlite(incident_id, payload)

    # Create a text summary to index
    text = json.dumps(payload)
    vector = _generate_vector(text)

    # Index into Qdrant (best-effort)
    indexed = _index_qdrant(incident_id, text, vector)

    # Simple rule-based "patterns" (placeholder)
    patterns = []
    if payload.get("severity") in ("High", "Critical"):
        patterns.append({"type": "high_severity", "detail": "High severity incident"})

    recommendations = []
    if payload.get("resource_urgency") == "High":
        recommendations.append("Prioritize resource dispatch and staging")

    return LearningResponse(
        incident_id=incident_id,
        status="stored",
        patterns=patterns,
        recommendations=recommendations,
        persisted_id=persisted_id,
    )
