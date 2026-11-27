"""
Health Check and Service Diagnostics API Route.
"""

from typing import Optional
from fastapi import APIRouter, Header
from app.config import settings
from app.models.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health(
    x_gemini_api_key: Optional[str] = Header(default=None, alias="X-Gemini-Api-Key"),
):
    """
    Returns the backend service health status, active fetcher, and analyzer modes.
    """
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        fetcher=settings.active_fetcher,
        analyzer=settings.resolve_analyzer_mode(x_gemini_api_key),
    )
