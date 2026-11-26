import pytest
from app.services.fetchers.mock_fetcher import MockFetcher


@pytest.mark.asyncio
async def test_mock_fetcher():
    """Verifies the MockFetcher returns structured result with elapsed time."""
    fetcher = MockFetcher(simulated_delay_ms=20)
    result = await fetcher.fetch("https://example.com/laptop-review")

    assert result.status == "ok"
    assert result.url == "https://example.com/laptop-review"
    assert "Example.com" in result.title or "Laptop" in result.title
    assert len(result.extracted_text) > 100
    assert result.error is None
    assert result.elapsed_ms >= 15
    await fetcher.close()
