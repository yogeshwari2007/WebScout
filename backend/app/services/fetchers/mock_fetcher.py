import asyncio
import time
from urllib.parse import urlsplit
from app.models.fetch import FetchResult
from app.services.fetchers.base import PageFetcher


class MockFetcher(PageFetcher):
    """
    Deterministic mock fetcher for testing, CI pipelines, and offline runs.
    Does not require network access or Playwright browser instances.
    """

    def __init__(self, simulated_delay_ms: int = 120):
        self.simulated_delay_ms = simulated_delay_ms

    async def fetch(self, url: str) -> FetchResult:
        start_time = time.monotonic()

        # Simulate network roundtrip latency
        if self.simulated_delay_ms > 0:
            await asyncio.sleep(self.simulated_delay_ms / 1000.0)

        parsed = urlsplit(url)
        hostname = parsed.hostname or "example.com"
        clean_name = hostname.replace("www.", "").capitalize()

        # Synthetic mock content based on URL
        sample_title = f"{clean_name} - In-Depth Product & Technology Analysis"
        sample_text = (
            f"# {sample_title}\n\n"
            f"Comprehensive testing and engineering specifications extracted from {hostname}.\n\n"
            f"## Specifications & Overview\n"
            f"• High-efficiency multi-core architecture with unified memory.\n"
            f"• Sustained 14-hour real-world developer battery benchmark.\n"
            f"• Ergonomic low-profile tactile keyboard with dual Thunderbolt 4 ports.\n\n"
            f"## Benchmarks & Evaluation\n"
            f"Single-threaded compilation performance exceeds rival ultrabooks by 18% in simulated builds. "
            f"Thermal dissipation remains quiet under standard developer workloads.\n\n"
            f"Source verified from {url}."
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return FetchResult(
            url=url,
            title=sample_title,
            extracted_text=sample_text,
            status="ok",
            error=None,
            elapsed_ms=elapsed_ms,
        )

    async def close(self) -> None:
        pass
