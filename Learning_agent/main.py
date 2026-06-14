"""
Learning Agent - FastAPI Application
Provides lightweight learning, indexing to Qdrant, and knowledge persistence.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from learning_engine import analyze_and_store, LearningRequest, LearningResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Learning Agent",
    version="0.1.0",
    description="Learning and knowledge base agent for disaster intelligence",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"service": "Learning Agent", "status": "running"}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "learning_agent"}


@app.post("/api/v1/learning/analyze", response_model=LearningResponse)
async def analyze(request: LearningRequest):
    try:
        logger.info(f"[Learning] Analyze request for {request.incident_id}")
        response = analyze_and_store(request)
        return response
    except Exception as e:
        logger.error(f"[Learning] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
