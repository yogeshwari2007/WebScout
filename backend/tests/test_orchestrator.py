import pytest
from app.services.fetchers.mock_fetcher import MockFetcher
from app.services.analyzers.mock_analyzer import MockAnalyzer
from app.services.orchestrator import ResearchOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_concurrent_success():
    """Verifies concurrent fetching preserves input order and synthesizes response."""
    fetcher = MockFetcher(simulated_delay_ms=30)
    analyzer = MockAnalyzer()
    orchestrator = ResearchOrchestrator(fetcher, analyzer)

    urls = [
        "https://example.com/source1",
        "https://example.org/source2",
        "https://example.net/source3",
    ]

    response = await orchestrator.execute_research(
        query="Best lightweight laptops for students in 2026",
        urls=urls,
    )

    assert response.query == "Best lightweight laptops for students in 2026"
    assert len(response.sources) == 3
    assert [s.url for s in response.sources] == urls
    assert all(s.status == "ok" for s in response.sources)
    assert len(response.items) == 3
    assert response.elapsed_ms > 0
    assert response.recommendation.winner != ""


@pytest.mark.asyncio
async def test_orchestrator_handles_partial_failure():
    """Verifies one invalid or failed URL does not cancel other fetches."""
    fetcher = MockFetcher(simulated_delay_ms=20)
    analyzer = MockAnalyzer()
    orchestrator = ResearchOrchestrator(fetcher, analyzer)

    urls = [
        "https://example.com/valid1",
        "http://127.0.0.1/internal",  # Blocked loopback private IP on standard port 80
        "https://example.org/valid2",
    ]

    response = await orchestrator.execute_research(
        query="Comparing laptop alternatives",
        urls=urls,
    )

    assert len(response.sources) == 3
    assert response.sources[0].status == "ok"
    assert response.sources[1].status == "failed"
    assert response.sources[1].error is not None
    assert "private" in response.sources[1].error.lower() or "blocked" in response.sources[1].error.lower() or "restricted" in response.sources[1].error.lower()
    assert response.sources[2].status == "ok"

    # Analysis still generates based on the 2 successful sources
    assert len(response.items) == 2


@pytest.mark.asyncio
async def test_orchestrator_handles_all_failed():
    """Verifies that when all sources fail, orchestrator returns clean response without crashing."""
    fetcher = MockFetcher(simulated_delay_ms=10)
    analyzer = MockAnalyzer()
    orchestrator = ResearchOrchestrator(fetcher, analyzer)

    urls = [
        "http://localhost:8000",
        "file:///etc/hosts",
    ]

    response = await orchestrator.execute_research(
        query="Testing complete failure tolerance",
        urls=urls,
    )

    assert len(response.sources) == 2
    assert all(s.status == "failed" for s in response.sources)
    assert "Unable to generate synthesis" in response.summary
    assert len(response.items) == 0
