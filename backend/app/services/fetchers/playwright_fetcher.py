import asyncio
import logging
import time
from typing import Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
    Route,
    Request,
)

from app.config import settings
from app.models.fetch import FetchResult
from app.services.fetchers.base import PageFetcher
from app.utils.content_cleaner import clean_html
from app.utils.url_validation import validate_url

logger = logging.getLogger("webscout.fetcher")

# Resource types blocked for speed and memory efficiency
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}


class PlaywrightFetcher(PageFetcher):
    """
    Production-grade website fetcher using headless Chromium via Playwright.
    Features:
    - Persistent, reusable browser instance
    - Route interception (blocks images, media, fonts to save memory & bandwidth)
    - Runtime SSRF route guarding on requests and redirects
    - 20-second hard navigation timeout per page
    - Clean DOM extraction and text sanitization
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Initializes the Playwright Chromium browser instance if not already running."""
        async with self._lock:
            if self._browser is None or not self._browser.is_connected():
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--no-zygote",
                        "--disable-extensions",
                    ],
                )
                logger.info("Playwright Chromium browser started successfully.")

    async def _handle_route(self, route: Route, request: Request) -> None:
        """
        Intercepts network requests to:
        1. Block bandwidth-heavy resources (images, media, fonts)
        2. Block SSRF attempts via scripts or iframe/redirect navigations
        """
        url = request.url

        # Check for dangerous schemes
        if url.startswith(("file:", "data:", "javascript:")):
            await route.abort("blockedbyclient")
            return

        # Check resource type
        if request.resource_type in BLOCKED_RESOURCE_TYPES:
            await route.abort("blockedbyclient")
            return

        # Revalidate destination for anti-SSRF protection on subrequests/redirects
        if request.is_navigation_request():
            is_valid, _, _ = validate_url(url, resolve_dns=True)
            if not is_valid:
                logger.warning("Blocked navigation request to restricted destination: %s", url)
                await route.abort("blockedbyclient")
                return

        await route.continue_()

    async def fetch(self, url: str) -> FetchResult:
        """
        Asynchronously navigates to the URL, blocks non-essential resources,
        and extracts cleaned readable content.
        """
        if self._browser is None or not self._browser.is_connected():
            await self.start()

        assert self._browser is not None

        start_time = time.monotonic()
        context = None
        page = None

        try:
            # Create an isolated context per fetch
            context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36 WebScout/1.0"
                ),
                java_script_enabled=True,
                ignore_https_errors=False,
            )

            page = await context.new_page()

            # Enable resource interception and runtime SSRF blocking
            await page.route("**/*", self._handle_route)

            # Navigate with 20s timeout, waiting for DOM readiness
            timeout_ms = settings.NAVIGATION_TIMEOUT_MS
            response = await page.goto(
                url,
                timeout=timeout_ms,
                wait_until="domcontentloaded",
            )

            # Wait briefly for dynamic JavaScript rendering
            await asyncio.sleep(0.6)

            # Check HTTP status code
            if response and response.status >= 400:
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                return FetchResult(
                    url=url,
                    title="Website Unavailable",
                    extracted_text="",
                    status="failed",
                    error=f"Destination returned HTTP status {response.status}",
                    elapsed_ms=elapsed_ms,
                )

            # Extract rendered HTML content
            html = await page.content()

            # Clean and parse content using BeautifulSoup
            title, cleaned_text = clean_html(html, max_chars=settings.MAX_EXTRACTED_CHARS)

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            # Verify meaningful content was extracted
            if not cleaned_text or len(cleaned_text.strip()) < 50:
                return FetchResult(
                    url=url,
                    title=title or "Empty Content",
                    extracted_text="",
                    status="failed",
                    error="Page contained no readable text or content was protected by a paywall/bot check.",
                    elapsed_ms=elapsed_ms,
                )

            return FetchResult(
                url=url,
                title=title,
                extracted_text=cleaned_text,
                status="ok",
                error=None,
                elapsed_ms=elapsed_ms,
            )

        except PlaywrightTimeoutError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return FetchResult(
                url=url,
                title="Navigation Timeout",
                extracted_text="",
                status="failed",
                error=f"Navigation timed out after {settings.NAVIGATION_TIMEOUT_MS / 1000:.0f} seconds.",
                elapsed_ms=elapsed_ms,
            )

        except PlaywrightError as pe:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            err_msg = str(pe)
            # Provide clean, safe error messages without internal stack traces
            if "blockedbyclient" in err_msg.lower():
                safe_err = "Navigation was blocked by security policy."
            elif "net::ERR_NAME_NOT_RESOLVED" in err_msg:
                safe_err = "Domain name could not be resolved by browser."
            elif "net::ERR_CONNECTION_REFUSED" in err_msg:
                safe_err = "Connection refused by destination server."
            else:
                safe_err = "Failed to load target website."

            return FetchResult(
                url=url,
                title="Fetch Error",
                extracted_text="",
                status="failed",
                error=safe_err,
                elapsed_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            logger.error("Unexpected fetch exception for %s: %s", url, e)
            return FetchResult(
                url=url,
                title="Fetch Error",
                extracted_text="",
                status="failed",
                error="An unexpected error occurred during website retrieval.",
                elapsed_ms=elapsed_ms,
            )

        finally:
            if page is not None:
                try:
                    await page.close()
                except Exception:
                    pass
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass

    async def close(self) -> None:
        """Closes the browser instance and Playwright driver."""
        async with self._lock:
            if self._browser is not None:
                try:
                    await self._browser.close()
                except Exception as e:
                    logger.warning("Error closing Playwright browser: %s", e)
                self._browser = None

            if self._playwright is not None:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    logger.warning("Error stopping Playwright driver: %s", e)
                self._playwright = None

            logger.info("Playwright Chromium browser shut down cleanly.")
