"""Health check and other API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint - no authentication required."""
    return {"status": "ok"}
