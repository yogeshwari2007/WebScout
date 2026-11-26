"""
Manual Integration Test Script.

Visits live public websites concurrently using the PlaywrightFetcher,
extracts and cleans content with BeautifulSoup, and outputs the structured results.

Run with:
  python tests/manual_integration_test.py
"""

import asyncio
import os
import sys
import time

# Ensure backend directory is in Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.fetchers.playwright_fetcher import PlaywrightFetcher


async def run_manual_test():
    print("=" * 70)
    print("WebScout Backend: Manual Playwright Integration Test")
    print("=" * 70)

    test_urls = [
        "https://example.com",
        "https://en.wikipedia.org/wiki/Web_crawler",
    ]

    fetcher = PlaywrightFetcher()
    print("\n[1] Starting Playwright Chromium instance...")
    start_total = time.monotonic()
    await fetcher.start()

    print(f"[2] Concurrently fetching {len(test_urls)} public websites...")
    tasks = [fetcher.fetch(url) for url in test_urls]
    results = await asyncio.gather(*tasks)

    print(f"\n[3] Inspection of Extracted Content:")
    for idx, r in enumerate(results, 1):
        print("-" * 60)
        print(f"Website #{idx}: {r.url}")
        print(f"Status:       {r.status}")
        print(f"Elapsed:      {r.elapsed_ms}ms")
        print(f"Title:        {r.title}")
        print(f"Text Length:  {len(r.extracted_text)} characters")
        if r.status == "ok":
            snippet = r.extracted_text[:200].replace("\n", " ").strip()
            print(f"Text Sample:  \"{snippet}...\"")
        else:
            print(f"Error:        {r.error}")

    print("\n[4] Shutting down Playwright browser...")
    await fetcher.close()

    total_duration = time.monotonic() - start_total
    print(f"\n[PASS] Manual integration test completed in {total_duration:.2f}s.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_manual_test())
