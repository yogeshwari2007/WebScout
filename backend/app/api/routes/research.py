"""
Research Execution API Route.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from app.models.request import ResearchRequest
from app.models.response import ResearchResponse
from app.services.orchestrator import get_orchestrator
from app.utils.url_validation import normalize_canonical_url

logger = logging.getLogger("webscout.api.research")
router = APIRouter()


@router.post(
    "/research",
    response_model=ResearchResponse,
    status_code=status.HTTP_200_OK,
    tags=["Research"],
    summary="Execute multi-website research request",
)
async def post_research(
    request: ResearchRequest,
    x_gemini_api_key: Optional[str] = Header(default=None, alias="X-Gemini-Api-Key"),
):
    """
    Accepts a research query and 1-5 candidate URLs, validates destinations,
    concurrently fetches page contents with anti-SSRF protections and timeouts,
    and returns synthesized research intelligence.
    """
    # Check for duplicate canonical URLs in the request
    seen_canonicals = set()
    for url in request.urls:
        canonical = normalize_canonical_url(url)
        if canonical in seen_canonicals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate canonical URL supplied: '{url}'. Please supply unique target websites.",
            )
        seen_canonicals.add(canonical)

    try:
        orchestrator = get_orchestrator(gemini_api_key=x_gemini_api_key)
        result = await orchestrator.execute_research(
            query=request.query, urls=request.urls
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in /api/research endpoint: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while executing research session.",
        )
