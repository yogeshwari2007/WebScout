"""
Research Orchestrator Service.

Coordinates URL validation, bounded concurrent website fetching (up to 5 concurrent
tasks via asyncio.Semaphore), error isolation, order preservation, analysis synthesis,
and structured response formatting.
"""

import asyncio
import logging
import time
from typing import List, Optional

from app.config import settings
from app.models.fetch import FetchResult
from app.models.response import (
    ComparisonItemResponse,
    RecommendationResponse,
    ResearchResponse,
    SourceStatusResponse,
)
from app.services.analyzers.base import BaseAnalyzer
from app.services.analyzers.mock_analyzer import MockAnalyzer
from app.services.analyzers.gemini_analyzer import GeminiAnalyzer
from app.services.fetchers.base import PageFetcher
from app.services.fetchers.mock_fetcher import MockFetcher
from app.services.fetchers.playwright_fetcher import PlaywrightFetcher
from app.utils.url_validation import validate_url

logger = logging.getLogger("webscout.orchestrator")


class ResearchOrchestrator:
    def __init__(self, fetcher: PageFetcher, analyzer: BaseAnalyzer):
        self.fetcher = fetcher
        self.analyzer = analyzer

    async def execute_research(
        self, query: str, urls: List[str]
    ) -> ResearchResponse:
        """
        Executes an end-to-end multi-website research request:
        1. Validates each URL (rejecting private IPs, localhost, bad ports, etc.).
        2. Detects duplicate canonical URLs.
        3. Concurrently fetches valid URLs (max 5 simultaneous) with isolated timeouts.
        4. Synthesizes findings using the configured analyzer.
        5. Returns structured ResearchResponse preserving input order.
        """
        start_time = time.monotonic()
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_FETCHES)

        # 1. Pre-validation of input URLs
        validated_specs = []
        seen_canonicals = set()

        for raw_url in urls:
            is_valid, error_msg, canonical = validate_url(raw_url, resolve_dns=True)

            if is_valid and canonical:
                if canonical in seen_canonicals:
                    validated_specs.append((raw_url, False, "Duplicate URL in request."))
                else:
                    seen_canonicals.add(canonical)
                    validated_specs.append((raw_url, True, None))
            else:
                validated_specs.append((raw_url, False, error_msg or "Invalid URL."))

        # 2. Worker coroutine per URL
        async def fetch_target(
            target_url: str, is_valid: bool, val_error: Optional[str]
        ) -> FetchResult:
            if not is_valid:
                return FetchResult(
                    url=target_url,
                    title="Validation Error",
                    extracted_text="",
                    status="failed",
                    error=val_error or "URL validation failed",
                    elapsed_ms=0,
                )

            async with semaphore:
                try:
                    # Guard fetch execution with timeout (25s hard ceiling to allow 20s internal navigation)
                    return await asyncio.wait_for(
                        self.fetcher.fetch(target_url), timeout=25.0
                    )
                except asyncio.TimeoutError:
                    return FetchResult(
                        url=target_url,
                        title="Navigation Timeout",
                        extracted_text="",
                        status="failed",
                        error="Fetching timed out after 20 seconds.",
                        elapsed_ms=int(settings.NAVIGATION_TIMEOUT_MS),
                    )
                except Exception as e:
                    logger.error("Unhandled error fetching %s: %s", target_url, e)
                    return FetchResult(
                        url=target_url,
                        title="Fetch Failure",
                        extracted_text="",
                        status="failed",
                        error="An unexpected error occurred while loading this website.",
                        elapsed_ms=0,
                    )

        # 3. Concurrently execute all fetches while preserving order
        fetch_tasks = [
            fetch_target(url, is_valid, err)
            for (url, is_valid, err) in validated_specs
        ]
        fetch_results: List[FetchResult] = await asyncio.gather(*fetch_tasks)

        # 4. Invoke Analyzer on results
        analysis_data = await self.analyzer.analyze(query, fetch_results)

        total_elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # 5. Format response adhering to API contract
        return ResearchResponse(
            query=query,
            summary=analysis_data.get("summary", ""),
            criteria=analysis_data.get("criteria", []),
            items=[
                ComparisonItemResponse(**item)
                for item in analysis_data.get("items", [])
            ],
            recommendation=RecommendationResponse(
                **analysis_data.get(
                    "recommendation",
                    {
                        "winner": "Unknown",
                        "reasoning": "No recommendation generated",
                        "source_urls": [],
                    },
                )
            ),
            sources=[
                SourceStatusResponse(
                    url=res.url,
                    title=res.title,
                    status=res.status,
                    error=res.error,
                )
                for res in fetch_results
            ],
            elapsed_ms=total_elapsed_ms,
        )


# Global instances for reuse across HTTP requests
_shared_playwright_fetcher: Optional[PlaywrightFetcher] = None
_shared_mock_fetcher: Optional[MockFetcher] = None
_shared_mock_analyzer: Optional[MockAnalyzer] = None
_shared_gemini_analyzer: Optional[GeminiAnalyzer] = None


def get_playwright_fetcher() -> PlaywrightFetcher:
    global _shared_playwright_fetcher
    if _shared_playwright_fetcher is None:
        _shared_playwright_fetcher = PlaywrightFetcher()
    return _shared_playwright_fetcher


def get_mock_fetcher() -> MockFetcher:
    global _shared_mock_fetcher
    if _shared_mock_fetcher is None:
        _shared_mock_fetcher = MockFetcher()
    return _shared_mock_fetcher


def get_mock_analyzer() -> MockAnalyzer:
    global _shared_mock_analyzer
    if _shared_mock_analyzer is None:
        _shared_mock_analyzer = MockAnalyzer()
    return _shared_mock_analyzer


def get_gemini_analyzer() -> BaseAnalyzer:
    global _shared_gemini_analyzer
    if settings.GEMINI_API_KEY:
        if _shared_gemini_analyzer is None:
            _shared_gemini_analyzer = GeminiAnalyzer(api_key=settings.GEMINI_API_KEY)
        return _shared_gemini_analyzer
    return get_mock_analyzer()


def get_orchestrator() -> ResearchOrchestrator:
    """
    Factory creating a ResearchOrchestrator wired with the configured fetcher and analyzer.
    """
    if settings.active_fetcher == "mock":
        fetcher = get_mock_fetcher()
    else:
        fetcher = get_playwright_fetcher()

    if settings.ANALYZER.lower() == "gemini" and settings.GEMINI_API_KEY:
        analyzer = get_gemini_analyzer()
    else:
        analyzer = get_mock_analyzer()

    return ResearchOrchestrator(fetcher=fetcher, analyzer=analyzer)
