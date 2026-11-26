"""
Health Check and Service Diagnostics API Route.
"""

from fastapi import APIRouter
from app.config import settings
from app.models.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """
    Returns the backend service health status, active fetcher, and analyzer modes.
    """
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        fetcher=settings.active_fetcher,
        analyzer=settings.ANALYZER,
    )
