"""
WebScout - Browser Automation & Content Extraction Engine
Uses Playwright (Headless Chromium) and BeautifulSoup4 to autonomously navigate,
render dynamic web pages, extract clean semantic content, and handle site errors gracefully.
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from utils import is_valid_http_url, sanitize_text_for_ai

logger = logging.getLogger("WebScoutScraper")
logger.setLevel(logging.INFO)


class ScrapedSource:
    """Represents the scraped evidence and metadata from a single target website."""
    def __init__(self, url: str):
        self.url = url
        self.title: str = ""
        self.status: str = "PENDING"  # SUCCESS, TIMEOUT, BLOCKED, ERROR, INVALID_URL
        self.error_message: Optional[str] = None
        self.content_text: str = ""
        self.headings: List[str] = []
        self.key_snippets: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.character_count: int = 0
        self.fetch_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "status": self.status,
            "error_message": self.error_message,
            "content_text": self.content_text,
            "headings": self.headings,
            "key_snippets": self.key_snippets,
            "metadata": self.metadata,
            "character_count": self.character_count,
            "fetch_duration_seconds": round(self.fetch_duration_seconds, 2)
        }


def clean_html_with_bs4(html_content: str, max_chars: int = 18000) -> Dict[str, Any]:
    """
    Parses rendered HTML with BeautifulSoup4.
    Strips noise (scripts, styles, nav, footers, cookie banners, ads).
    Extracts structured headings, paragraphs, lists, and main textual content.
    """
    if not html_content:
        return {"title": "No Title", "text": "", "headings": [], "snippets": []}

    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    if not title:
        title = "Web Page"

    # Remove non-content tags
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    # Remove elements matching common noise classes or IDs (cookie banners, ads, popups)
    noise_patterns = re.compile(
        r"(cookie|banner|consent|advertisement|ad-container|modal|popup|newsletter|privacy-notice)",
        re.I
    )
    for noisy in soup.find_all(attrs={"class": noise_patterns}):
        noisy.decompose()
    for noisy in soup.find_all(attrs={"id": noise_patterns}):
        noisy.decompose()

    # Extract prominent headings
    headings: List[str] = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        h_text = h.get_text(separator=" ", strip=True)
        if h_text and len(h_text) > 3 and h_text not in headings:
            headings.append(h_text[:120])
        if len(headings) >= 12:
            break

    # Prioritize main content areas if present
    main_container = soup.find("main") or soup.find("article") or soup.find(id=re.compile(r"(content|main|article)", re.I))
    target_root = main_container if main_container else soup.body or soup

    # Extract meaningful blocks: headings, paragraphs, list items, table rows
    snippets: List[str] = []
    collected_blocks = []

    for elem in target_root.find_all(["h1", "h2", "h3", "h4", "p", "li", "tr"]):
        block_text = elem.get_text(separator=" ", strip=True)
        # Filter out short or repetitive snippets
        if len(block_text) > 25:
            # Avoid duplicate lines
            if block_text not in collected_blocks:
                collected_blocks.append(block_text)
                if len(snippets) < 8 and len(block_text) > 40:
                    snippets.append(block_text[:200])

    full_extracted_text = "\n\n".join(collected_blocks)
    sanitized = sanitize_text_for_ai(full_extracted_text, max_chars=max_chars)

    return {
        "title": title,
        "text": sanitized,
        "headings": headings,
        "snippets": snippets
    }


def scrape_single_url_playwright(url: str, timeout_ms: int = 25000, max_chars: int = 18000) -> ScrapedSource:
    """
    Navigates to a single URL using Playwright Chromium with robust timeouts,
    stealth user-agent headers, and structured BeautifulSoup parsing.
    """
    source = ScrapedSource(url)
    start_time = time.time()

    # Validate URL first
    is_valid, reason = is_valid_http_url(url)
    if not is_valid:
        source.status = "INVALID_URL"
        source.error_message = reason
        source.fetch_duration_seconds = time.time() - start_time
        return source

    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            # Configure realistic browser context
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 WebScout/1.0",
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
                ignore_https_errors=True
            )
            page = context.new_page()

            # Set timeout
            page.set_default_navigation_timeout(timeout_ms)
            page.set_default_timeout(timeout_ms)

            try:
                # Navigate: domcontentloaded is faster and safer than waiting for full networkidle
                response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                
                # Brief wait for any initial client-side hydration
                page.wait_for_timeout(1000)

                http_status = response.status if response else 200
                if http_status in (401, 403, 429):
                    source.status = "BLOCKED"
                    source.error_message = f"HTTP {http_status} (Access restricted or rate limited by destination server)"
                elif http_status >= 400:
                    source.status = "ERROR"
                    source.error_message = f"HTTP {http_status} server error"

                # Capture rendered HTML
                html = page.content()
                parsed = clean_html_with_bs4(html, max_chars=max_chars)

                source.title = parsed["title"]
                source.content_text = parsed["text"]
                source.headings = parsed["headings"]
                source.key_snippets = parsed["snippets"]
                source.character_count = len(source.content_text)

                if source.status == "PENDING":
                    if source.character_count > 100:
                        source.status = "SUCCESS"
                    else:
                        source.status = "PARTIAL"
                        source.error_message = "Page loaded but minimal readable text was extracted."

            except PlaywrightTimeoutError:
                # If timeout happens during navigation, attempt to grab whatever DOM was partially rendered
                try:
                    partial_html = page.content()
                    parsed = clean_html_with_bs4(partial_html, max_chars=max_chars)
                    if len(parsed["text"]) > 200:
                        source.title = parsed["title"]
                        source.content_text = parsed["text"]
                        source.headings = parsed["headings"]
                        source.key_snippets = parsed["snippets"]
                        source.character_count = len(source.content_text)
                        source.status = "PARTIAL"
                        source.error_message = f"Navigation timed out after {timeout_ms//1000}s, but partial content was retrieved."
                    else:
                        source.status = "TIMEOUT"
                        source.error_message = f"Connection timed out ({timeout_ms//1000}s) while loading {url}."
                except Exception:
                    source.status = "TIMEOUT"
                    source.error_message = f"Navigation timed out after {timeout_ms//1000}s."
            except Exception as nav_err:
                source.status = "ERROR"
                source.error_message = f"Navigation failed: {str(nav_err)}"
            finally:
                context.close()
                browser.close()

    except Exception as e:
        source.status = "ERROR"
        source.error_message = f"Browser automation error: {str(e)}"

    source.fetch_duration_seconds = time.time() - start_time
    return source


def scrape_multiple_urls(urls: List[str], progress_callback=None, timeout_ms: int = 25000) -> List[ScrapedSource]:
    """
    Iterates through a list of URLs, navigates to each sequentially,
    records results, and invokes optional progress callback.
    Guarantees that one site's failure never crashes the whole research session.
    """
    results: List[ScrapedSource] = []
    total = len(urls)

    for idx, url in enumerate(urls, start=1):
        if progress_callback:
            progress_callback(idx, total, url, "navigating")

        logger.info(f"Navigating to [{idx}/{total}]: {url}")
        scraped = scrape_single_url_playwright(url, timeout_ms=timeout_ms)
        results.append(scraped)

        if progress_callback:
            progress_callback(idx, total, url, scraped.status)

    return results
