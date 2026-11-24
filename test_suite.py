"""
WebScout Automated Verification & QA Test Suite
Tests URL validation, SSRF filters, Playwright headless extraction,
BeautifulSoup parsing, AI engine structuring, and end-to-end pipeline execution.
"""

import sys
import unittest
from utils import is_valid_http_url, validate_research_inputs, generate_markdown_report
from scraper import scrape_single_url_playwright, clean_html_with_bs4
from ai_engine import clean_json_response, StructuredResearchReport, generate_local_heuristic_report
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
