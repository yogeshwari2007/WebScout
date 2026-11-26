"""
WebScout Automated Verification & QA Test Suite
Tests URL validation, SSRF filters, Playwright headless extraction,
BeautifulSoup parsing, AI engine structuring, and end-to-end pipeline execution.
"""

import sys
import unittest
from utils import is_valid_http_url, validate_research_inputs, generate_markdown_report
from scraper import scrape_single_url_playwright, clean_html_with_bs4
from ai_engine import clean_json_response, StructuredResearchReport, generate_local_heuristic_report, format_evidence_block, analyze_with_gemini
from analyzer import ResearchSession


class TestWebScoutSuite(unittest.TestCase):

    def test_01_url_validation_allowed(self):
        """Test valid HTTP/HTTPS URLs pass validation."""
        valid_urls = [
            "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "http://example.com",
            "https://www.google.com/search?q=test"
        ]
        for url in valid_urls:
            ok, reason = is_valid_http_url(url)
            self.assertTrue(ok, f"Expected {url} to be valid, got: {reason}")

    def test_02_url_validation_blocked_schemes_and_ssrf(self):
        """Test unsafe schemes, localhost, and private network IPs are blocked."""
        blocked_urls = [
            ("ftp://ftp.example.com", ["Unsupported scheme", "blocked"]),
            ("file:///etc/passwd", ["Unsupported scheme", "blocked"]),
            ("javascript:alert(1)", ["Unsupported scheme", "blocked"]),
            ("http://localhost:8000", ["localhost", "blocked"]),
            ("http://127.0.0.1:5000", ["localhost", "loopback", "blocked"]),
            ("http://192.168.1.1/admin", ["private", "loopback", "restricted", "blocked"]),
            ("http://10.0.0.1/status", ["private", "loopback", "restricted", "blocked"]),
            ("http://169.254.169.254/latest/meta-data/", ["metadata", "private", "blocked"]),
        ]
        for url, expected_keywords in blocked_urls:
            ok, reason = is_valid_http_url(url)
            self.assertFalse(ok, f"URL {url} should be blocked!")
            matched = any(kw.lower() in reason.lower() for kw in expected_keywords)
            self.assertTrue(matched, f"Reason '{reason}' did not match any of {expected_keywords}")

    def test_03_research_inputs_enforcement(self):
        """Test that minimum 2 URLs and valid queries are enforced."""
        # Less than 2 URLs
        ok, errors = validate_research_inputs("Valid Question Here", ["https://example.com"])
        self.assertFalse(ok)
        self.assertTrue(any("at least 2 distinct" in e for e in errors))

        # Short query
        ok, errors = validate_research_inputs("Hi", ["https://example.com", "https://example.org"])
        self.assertFalse(ok)
        self.assertTrue(any("at least 5 characters" in e for e in errors))

        # Duplicate URLs
        ok, errors = validate_research_inputs(
            "Valid Question Here",
            ["https://example.com", "https://example.com"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("Duplicate URL" in e for e in errors))

    def test_04_bs4_html_cleaning(self):
        """Test that BeautifulSoup cleans noise, removes scripts, and extracts titles & headings."""
        sample_html = """
        <html>
            <head><title>Test Laptop Review</title></head>
            <body>
                <nav><a href="#">Home</a><a href="#">About</a></nav>
                <div class="cookie-banner">Please accept all cookies!</div>
                <script>alert("ignore this script");</script>
                <main>
                    <h1>Dell XPS 15 Overview</h1>
                    <h2>Hardware Specs</h2>
                    <p>The Dell XPS 15 features an Intel Core i7 processor with 16GB of DDR5 RAM.</p>
                    <p>Battery life tested at approximately 10 hours under typical development workloads.</p>
                </main>
                <footer>Copyright 2026 Laptop Reviews Inc.</footer>
            </body>
        </html>
        """
        parsed = clean_html_with_bs4(sample_html)
        self.assertEqual(parsed["title"], "Test Laptop Review")
        self.assertIn("Dell XPS 15 Overview", parsed["headings"])
        self.assertIn("Intel Core i7", parsed["text"])
        self.assertNotIn("Please accept all cookies", parsed["text"])
        self.assertNotIn("alert", parsed["text"])

    def test_05_playwright_real_navigation(self):
        """Test real Playwright headless navigation on an accessible public site."""
        test_url = "https://example.com"
        scraped = scrape_single_url_playwright(test_url, timeout_ms=15000)
        self.assertEqual(scraped.status, "SUCCESS")
        self.assertIn("Example Domain", scraped.title)
        self.assertGreater(scraped.character_count, 50)
        self.assertGreater(scraped.fetch_duration_seconds, 0)

    def test_06_playwright_failure_tolerance(self):
        """Test that an unresolvable or dead domain fails gracefully without raising an unhandled exception."""
        dead_url = "https://this-domain-does-not-exist-at-all-xyz987654321.com"
        scraped = scrape_single_url_playwright(dead_url, timeout_ms=10000)
        self.assertIn(scraped.status, ("ERROR", "TIMEOUT"))
        self.assertIsNotNone(scraped.error_message)

    def test_07_ai_response_cleaning_and_pydantic_validation(self):
        """Test markdown code fence stripping and Pydantic schema validation."""
        fenced_json = """```json
        {
            "research_summary": "Summary of laptops for students.",
            "source_findings": [
                {
                    "source_title": "MacBook Air Review",
                    "source_url": "https://example.com/macbook",
                    "key_findings": ["M2 Chip", "18-hour battery life"],
                    "evidence_snippets": ["Battery lasts 18 hours."]
                }
            ],
            "comparison_matrix": [
                {
                    "criterion": "Battery Life",
                    "source_evaluations": {"MacBook Air": "18 hours"},
                    "synthesis_note": "Industry leading longevity."
                }
            ],
            "discrepancies": [],
            "pros_and_cons": [
                {
                    "source_name": "MacBook Air",
                    "advantages": ["Long battery"],
                    "disadvantages": ["Base model has 8GB RAM"]
                }
            ],
            "recommendation": {
                "verdict": "MacBook Air is the top choice for battery and portability.",
                "reasoning": "Exceeds runtime requirements for students.",
                "top_choice_or_conclusion": "MacBook Air",
                "supporting_sources": ["https://example.com/macbook"]
            },
            "limitations": []
        }
        ```"""
        cleaned = clean_json_response(fenced_json)
        self.assertFalse(cleaned.startswith("```"))
        import json
        data = json.loads(cleaned)
        validated = StructuredResearchReport(**data)
        self.assertEqual(validated.recommendation.top_choice_or_conclusion, "MacBook Air")

    def test_08_end_to_end_research_session(self):
        """Test end-to-end multi-site workflow execution in ResearchSession."""
        session = ResearchSession(
            query="Compare Wikipedia articles on Python and Rust",
            urls=[
                "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "https://en.wikipedia.org/wiki/Rust_(programming_language)"
            ],
            preference="Syntax, Memory Safety, Performance"
        )
        report = session.execute()
        self.assertFalse(report.get("error", False))
        self.assertEqual(len(report.get("sources", [])), 2)
        self.assertIn("markdown_content", report)
        self.assertGreater(len(report["markdown_content"]), 100)
        self.assertIn("Python", report["markdown_content"])


    def test_09_evidence_formatting_successful_source(self):
        """Test that a SUCCESS source with usable content formats title, URL, headings, status, and content."""
        sources = [
            {
                "status": "SUCCESS",
                "url": "https://fastapi.tiangolo.com",
                "title": "FastAPI Documentation",
                "content_text": "FastAPI is a modern, fast web framework for building APIs with Python 3.8+.",
                "headings": ["Features", "Installation", "Tutorial"]
            }
        ]
        result = format_evidence_block(sources)
        self.assertIn("--- SOURCE 1: FastAPI Documentation ---", result)
        self.assertIn("URL: https://fastapi.tiangolo.com", result)
        self.assertIn("STATUS: SUCCESS", result)
        self.assertIn("HEADINGS: Features, Installation, Tutorial", result)
        self.assertIn("EXTRACTED CONTENT:\nFastAPI is a modern, fast web framework", result)
        self.assertNotIn("FAILED", result)
        self.assertNotIn("EXTRACTED CONTENT: None", result)

    def test_10_evidence_formatting_partial_with_content(self):
        """Test that a PARTIAL source with usable content contributes its content and is labeled as partial."""
        sources = [
            {
                "status": "PARTIAL",
                "url": "https://react.dev",
                "title": "React Reference",
                "content_text": "React lets you build user interfaces out of individual pieces called components.",
                "headings": ["Quick Start", "Hooks"],
                "error_message": "Navigation timed out after 15s, but partial content was retrieved."
            }
        ]
        result = format_evidence_block(sources)
        self.assertIn("--- SOURCE 1: React Reference ---", result)
        self.assertIn("URL: https://react.dev", result)
        self.assertIn("STATUS: PARTIAL", result)
        self.assertIn("Incomplete extraction", result)
        self.assertIn("HEADINGS: Quick Start, Hooks", result)
        self.assertIn("EXTRACTED CONTENT:\nReact lets you build user interfaces", result)
        self.assertNotIn("EXTRACTED CONTENT: None", result)

    def test_11_evidence_formatting_partial_empty_content(self):
        """Test that a PARTIAL source with empty or whitespace-only content does NOT contribute valid evidence."""
        empty_sources = [
            {
                "status": "PARTIAL",
                "url": "https://spa-blank.example.com",
                "title": "SPA Dynamic Shell",
                "content_text": "",
                "headings": [],
                "error_message": "Page loaded but minimal readable text was extracted."
            },
            {
                "status": "PARTIAL",
                "url": "https://whitespace.example.com",
                "title": "Whitespace Only",
                "content_text": "   \n\t   ",
                "headings": ["Header"],
                "error_message": "Page loaded but minimal readable text was extracted."
            }
        ]
        for src in empty_sources:
            result = format_evidence_block([src])
            self.assertIn("STATUS: FAILED (PARTIAL)", result)
            self.assertIn("EXTRACTED CONTENT: None", result)
            self.assertNotIn("EXTRACTED CONTENT:\n\n", result)

    def test_12_evidence_formatting_failed_statuses(self):
        """Test that failed sources (ERROR, TIMEOUT, BLOCKED, INVALID_URL) preserve reason and have no content."""
        failed_cases = [
            ("ERROR", "HTTP 500 server error"),
            ("TIMEOUT", "Navigation timed out after 25s"),
            ("BLOCKED", "HTTP 403 Forbidden - Access restricted"),
            ("INVALID_URL", "Host does not resolve to a valid domain")
        ]
        for idx, (status, err_msg) in enumerate(failed_cases, start=1):
            source = {
                "status": status,
                "url": f"https://fail-{status.lower()}.com",
                "title": f"Failed {status} Site",
                "error_message": err_msg,
                "content_text": ""
            }
            result = format_evidence_block([source])
            self.assertIn(f"STATUS: FAILED ({status}) - Reason: {err_msg}", result)
            self.assertIn("EXTRACTED CONTENT: None (Site could not be retrieved)", result)

    def test_13_evidence_formatting_mixed_sources(self):
        """Test formatting a realistic mix of SUCCESS, PARTIAL with content, PARTIAL empty, and ERROR."""
        sources = [
            {
                "status": "SUCCESS",
                "url": "https://python.org",
                "title": "Python Official",
                "content_text": "Python is a programming language that lets you work quickly.",
                "headings": ["About", "Downloads"]
            },
            {
                "status": "PARTIAL",
                "url": "https://docs.pydantic.dev",
                "title": "Pydantic Docs",
                "content_text": "Data validation using Python type hints.",
                "headings": ["Concepts", "Models"],
                "error_message": "Page hydration timed out"
            },
            {
                "status": "PARTIAL",
                "url": "https://empty-app.com",
                "title": "Empty Page",
                "content_text": "",
                "error_message": "No readable content extracted"
            },
            {
                "status": "BLOCKED",
                "url": "https://restricted.com",
                "title": "Restricted Portal",
                "error_message": "HTTP 403 (Access restricted)"
            }
        ]

        result = format_evidence_block(sources)
        blocks = result.split("\n\n")
        self.assertEqual(len(blocks), 4)

        # Source 1 (SUCCESS)
        self.assertIn("SOURCE 1: Python Official", blocks[0])
        self.assertIn("STATUS: SUCCESS", blocks[0])
        self.assertIn("Python is a programming language", blocks[0])

        # Source 2 (PARTIAL with content)
        self.assertIn("SOURCE 2: Pydantic Docs", blocks[1])
        self.assertIn("STATUS: PARTIAL", blocks[1])
        self.assertIn("Data validation using Python type hints.", blocks[1])

        # Source 3 (PARTIAL empty)
        self.assertIn("SOURCE 3: Empty Page", blocks[2])
        self.assertIn("STATUS: FAILED (PARTIAL)", blocks[2])
        self.assertIn("EXTRACTED CONTENT: None", blocks[2])

        # Source 4 (BLOCKED)
        self.assertIn("SOURCE 4: Restricted Portal", blocks[3])
        self.assertIn("STATUS: FAILED (BLOCKED)", blocks[3])
        self.assertIn("EXTRACTED CONTENT: None", blocks[3])

    def test_14_ai_engine_partial_source_integration(self):
        """Test that analyze_with_gemini and heuristic synthesis handle partial sources consistently."""
        unusable_sources = [
            {"status": "PARTIAL", "url": "https://empty.com", "content_text": ""},
            {"status": "ERROR", "url": "https://err.com", "error_message": "404 Not Found"}
        ]
        res_empty = analyze_with_gemini(
            query="Evaluate tools",
            sources=unusable_sources,
            api_key="mock_key"
        )
        self.assertTrue(res_empty.get("error", False))
        self.assertEqual(res_empty["recommendation"]["top_choice_or_conclusion"], "Inconclusive")

        usable_sources = [
            {
                "status": "PARTIAL",
                "url": "https://partial-usable.com",
                "title": "Partial Framework",
                "content_text": "This framework offers high concurrency and async execution.",
                "headings": ["Async Engine", "Benchmarks"],
                "key_snippets": ["Offers high concurrency"]
            },
            {
                "status": "ERROR",
                "url": "https://dead.com",
                "error_message": "DNS resolution failed"
            }
        ]
        report = generate_local_heuristic_report("Compare frameworks", usable_sources)
        self.assertFalse(report.get("error", True))
        self.assertEqual(len(report["source_findings"]), 1)
        self.assertEqual(report["source_findings"][0]["source_title"], "Partial Framework")
        self.assertTrue(any("Partial extraction" in lim for lim in report["limitations"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
