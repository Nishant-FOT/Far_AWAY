"""
Disaster Agent API - Main FastAPI Application
Aggregates all Disaster agents (GIS, Resource, Route, Communication, Feedback)
and exposes them as unified REST endpoints.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routes.gis_routes import router as gis_router
from routes.resource_routes import router as resource_router
from routes.route_routes import router as route_router
from routes.communication_routes import router as communication_router
from routes.feedback_routes import router as feedback_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Disaster Agents API",
    version="1.0.0",
    description="Unified API for GIS, Resource, Route, Communication, and Feedback agents",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gis_router)
app.include_router(resource_router)
app.include_router(route_router)
app.include_router(communication_router)
app.include_router(feedback_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Disaster Agents API",
        "version": "1.0.0",
        "status": "running",
        "agents": [
            "gis",
            "resource",
            "route",
            "communication",
            "feedback",
        ],
        "docs": "/api/docs",
    }


@app.get("/api/v1/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "disaster_agents_api",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
