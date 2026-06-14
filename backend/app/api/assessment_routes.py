from fastapi import APIRouter

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("/health")
def health_check():
    return {"status": "ok"}
