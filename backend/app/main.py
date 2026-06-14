import shared.early_init
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.command_router import router as command_router
from app.api.mock_disaster import router as mock_disaster_router

app = FastAPI(title="Command Center API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(command_router)
app.include_router(mock_disaster_router)
from app.api.mock_disaster import router2 as mock_public_router
app.include_router(mock_public_router)


@app.get("/")
def read_root():
    return {"message": "Disaster Intelligence Command Center Backend", "docs": "/docs"}
