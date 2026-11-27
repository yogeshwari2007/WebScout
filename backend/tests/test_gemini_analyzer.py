import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport

from app.config import Settings, settings
from app.main import app
from app.models.fetch import FetchResult
from app.models.response import ResearchResponse
from app.services.analyzers.gemini_analyzer import GeminiAnalyzer
from app.services.analyzers.mock_analyzer import MockAnalyzer
from app.services.fetchers.mock_fetcher import MockFetcher
from app.services.orchestrator import get_orchestrator, ResearchOrchestrator


def test_settings_active_analyzer_modes():
    """Settings.active_analyzer resolves cleanly across auto, gemini, mock, and USE_MOCK."""
    assert Settings(ANALYZER="auto", GEMINI_API_KEY=None).active_analyzer == "mock"
    assert Settings(ANALYZER="auto", GEMINI_API_KEY="").active_analyzer == "mock"
    assert Settings(ANALYZER="auto", GEMINI_API_KEY="your_gemini_api_key_here").active_analyzer == "mock"
    assert Settings(ANALYZER="auto", GEMINI_API_KEY="  fake-test-key  ").active_analyzer == "gemini"
    assert Settings(ANALYZER="gemini", GEMINI_API_KEY="fake-test-key").active_analyzer == "gemini"
    assert Settings(ANALYZER="gemini", GEMINI_API_KEY=None).active_analyzer == "mock"
    assert Settings(ANALYZER="mock", GEMINI_API_KEY="fake-test-key").active_analyzer == "mock"
    assert Settings(ANALYZER="auto", GEMINI_API_KEY="fake-test-key", USE_MOCK=True).active_analyzer == "mock"


@pytest.mark.asyncio
async def test_gemini_analyzer_semantic_synthesis_and_coercion():
    """GeminiAnalyzer parses fenced JSON and coerces non-string criteria values into valid ResearchResponse."""
    payload = {
        "summary": "Semantic comparison shows Framework A leads on async throughput while Framework B optimizes minimalism.",
        "criteria": ["Async Support", "Minimum Python", "Stars"],
        "items": [
            {
                "name": "Framework A",
                "source_url": "https://a.example.com",
                "values": {
                    "Async Support": True,
                    "Minimum Python": 3.10,
                    "Stars": None,
                },
                "pros": ["Native ASGI concurrency"],
                "cons": ["Smaller plugin ecosystem"],
            },
            {
                "name": "Framework B",
                "source_url": "https://b.example.com",
                "values": {
                    "Async Support": "Optional extension",
                    "Minimum Python": "3.9",
                    "Stars": 68000,
                },
                "pros": ["Mature synchronous ecosystem"],
                "cons": ["Less suited for heavy websockets"],
            },
        ],
        "recommendation": {
            "winner": "Framework A",
            "reasoning": "Best alignment with high-concurrency async API requirements.",
            "source_urls": ["https://a.example.com", "https://b.example.com"],
        },
    }

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = SimpleNamespace(
        text=f"```json\n{json.dumps(payload)}\n```"
    )

    sources = [
        FetchResult(
            url="https://a.example.com",
            title="Framework A Docs",
            extracted_text="Framework A supports native ASGI async handlers and requires Python 3.10+.",
            status="ok",
        ),
        FetchResult(
            url="https://b.example.com",
            title="Framework B Docs",
            extracted_text="Framework B is a lightweight WSGI microframework with 68000 GitHub stars.",
            status="ok",
        ),
    ]

    with patch("app.services.analyzers.gemini_analyzer.genai.Client", return_value=mock_client):
        analyzer = GeminiAnalyzer(api_key="fake-test-key")
        orchestrator = ResearchOrchestrator(MockFetcher(), analyzer)
        result = await analyzer.analyze("Compare async web frameworks", sources)

    # Validate coerced fields satisfy ResearchResponse contract
    model = ResearchResponse(
        query="Compare async web frameworks",
        summary=result["summary"],
        criteria=result["criteria"],
        items=result["items"],
        recommendation=result["recommendation"],
        sources=[],
        elapsed_ms=120,
    )
    assert model.items[0].values["Async Support"] == "True"
    assert model.items[0].values["Minimum Python"] == "3.1"
    assert model.items[0].values["Stars"] == "Not available"
    assert model.recommendation.winner == "Framework A"
    assert "[DEMO / MOCK ANALYSIS]" not in model.summary


@pytest.mark.asyncio
async def test_gemini_analyzer_falls_back_on_error_or_all_failed():
    """GeminiAnalyzer falls back gracefully to MockAnalyzer on API error or empty/failed fetches."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("Upstream quota exceeded")

    ok_sources = [
        FetchResult(
            url="https://a.example.com",
            title="Site A",
            extracted_text="Some clean extracted website text for testing fallback resilience.",
            status="ok",
        )
    ]
    failed_sources = [
        FetchResult(
            url="https://down.example.com",
            title="Timeout",
            extracted_text="",
            status="failed",
            error="Timed out",
        )
    ]

    with patch("app.services.analyzers.gemini_analyzer.genai.Client", return_value=mock_client):
        analyzer = GeminiAnalyzer(api_key="fake-test-key")

        # Error fallback
        err_result = await analyzer.analyze("Fallback on API error", ok_sources)
        assert "[DEMO / MOCK ANALYSIS]" in err_result["summary"]

        # All failed sources skips Gemini SDK entirely
        mock_client.models.generate_content.reset_mock()
        fail_result = await analyzer.analyze("All sources failed", failed_sources)
        mock_client.models.generate_content.assert_not_called()
        assert "Unable to generate synthesis" in fail_result["summary"]


@pytest.mark.asyncio
async def test_health_and_orchestrator_reflect_gemini_key():
    """/api/health and get_orchestrator report 'gemini' when key is configured in auto mode."""
    orig_analyzer = settings.ANALYZER
    orig_key = settings.GEMINI_API_KEY
    orig_mock = settings.USE_MOCK
    try:
        settings.ANALYZER = "auto"
        settings.USE_MOCK = False
        settings.GEMINI_API_KEY = "fake-test-key"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/health")
            assert res.status_code == 200
            assert res.json()["analyzer"] == "gemini"

        with patch("app.services.analyzers.gemini_analyzer.genai.Client", return_value=MagicMock()):
            orch = get_orchestrator()
            assert isinstance(orch.analyzer, GeminiAnalyzer)

        settings.GEMINI_API_KEY = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/health")
            assert res.status_code == 200
            assert res.json()["analyzer"] == "mock"
        assert isinstance(get_orchestrator().analyzer, MockAnalyzer)
    finally:
        settings.ANALYZER = orig_analyzer
        settings.GEMINI_API_KEY = orig_key
        settings.USE_MOCK = orig_mock
