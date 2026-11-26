import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verifies the service root endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["service"] == settings.PROJECT_NAME


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verifies the /api/health endpoint structure and values."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "fetcher" in data
        assert "analyzer" in data
        assert data["service"] == settings.PROJECT_NAME


@pytest.mark.asyncio
async def test_research_endpoint_validation_errors():
    """Verifies input validation: short query, empty URLs, >5 URLs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Query too short (<10 chars)
        res = await client.post("/api/research", json={"query": "Short", "urls": ["https://example.com"]})
        assert res.status_code == 422

        # 2. Empty URLs list
        res = await client.post("/api/research", json={"query": "Valid research query long enough", "urls": []})
        assert res.status_code == 422

        # 3. Exceeds max URLs (> 5)
        res = await client.post(
            "/api/research",
            json={
                "query": "Valid research query long enough",
                "urls": [
                    "https://example.com/1",
                    "https://example.com/2",
                    "https://example.com/3",
                    "https://example.com/4",
                    "https://example.com/5",
                    "https://example.com/6",
                ],
            },
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_research_endpoint_duplicate_urls_rejected():
    """Verifies that duplicate canonical URLs in a single request are rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/research",
            json={
                "query": "Testing duplicate canonical URL validation",
                "urls": [
                    "https://example.com/page",
                    "https://EXAMPLE.com:443/page#comments",  # Resolves to same canonical
                ],
            },
        )
        assert res.status_code == 400
        assert "Duplicate canonical URL" in res.json()["detail"]


@pytest.mark.asyncio
async def test_research_endpoint_contract_compliance():
    """Verifies the /api/research response matches the frontend contract."""
    # Force mock fetcher for fast CI testing
    orig_mock = settings.USE_MOCK
    settings.USE_MOCK = True

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(
                "/api/research",
                json={
                    "query": "Best ultrabooks for software development in 2026",
                    "urls": [
                        "https://example.com/macbook-air-m3",
                        "https://example.org/thinkpad-x1",
                    ],
                },
            )
            assert res.status_code == 200
            data = res.json()

            # Contract field checks
            assert "query" in data
            assert "summary" in data
            assert "criteria" in data and isinstance(data["criteria"], list)
            assert "items" in data and isinstance(data["items"], list)
            assert "recommendation" in data and isinstance(data["recommendation"], dict)
            assert "winner" in data["recommendation"]
            assert "reasoning" in data["recommendation"]
            assert "source_urls" in data["recommendation"]
            assert "sources" in data and isinstance(data["sources"], list)
            assert "elapsed_ms" in data and isinstance(data["elapsed_ms"], int)

            # Item structure
            for item in data["items"]:
                assert "name" in item
                assert "source_url" in item
                assert "values" in item and isinstance(item["values"], dict)
                assert "pros" in item and isinstance(item["pros"], list)
                assert "cons" in item and isinstance(item["cons"], list)

            # Source status structure
            for src in data["sources"]:
                assert "url" in src
                assert "title" in src
                assert src["status"] in ("ok", "failed")

    finally:
        settings.USE_MOCK = orig_mock
