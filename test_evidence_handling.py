"""
WebScout Evidence Handling & Evidence-Backed Findings Test Suite
Covers partial/failed source formatting and deterministic evidence grounding
(100% mocked, zero live network or Gemini API calls).
"""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest

from ai_engine import (
    ComparisonRow,
    StructuredResearchReport,
    analyze_with_gemini,
    assess_citation_relevance,
    format_evidence_block,
    generate_local_heuristic_report,
    verify_and_ground_report,
    verify_excerpt_in_source,
)
from analyzer import ResearchSession
from scraper import ScrapedSource
from utils import generate_markdown_report


def _mock_genai_response(payload: dict):
    """Creates a mock google.genai Client that returns `payload` as JSON text."""
    mock_client = MagicMock()
    mock_response = SimpleNamespace(text=json.dumps(payload))
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


class TestEvidenceHandling(unittest.TestCase):

    def test_successful_source_evidence_formatting(self):
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

    def test_partial_source_with_extracted_content(self):
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

    def test_partial_source_when_content_is_empty(self):
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

    def test_failed_source_statuses(self):
        """Test that failed sources (ERROR, TIMEOUT, BLOCKED, INVALID_URL) preserve reason and have no content."""
        failed_cases = [
            ("ERROR", "HTTP 500 server error"),
            ("TIMEOUT", "Navigation timed out after 25s"),
            ("BLOCKED", "HTTP 403 Forbidden - Access restricted"),
            ("INVALID_URL", "Host does not resolve to a valid domain")
        ]
        for status, err_msg in failed_cases:
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

    def test_mixed_source_inputs(self):
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

        self.assertIn("SOURCE 1: Python Official", blocks[0])
        self.assertIn("STATUS: SUCCESS", blocks[0])
        self.assertIn("Python is a programming language", blocks[0])

        self.assertIn("SOURCE 2: Pydantic Docs", blocks[1])
        self.assertIn("STATUS: PARTIAL", blocks[1])
        self.assertIn("Data validation using Python type hints.", blocks[1])

        self.assertIn("SOURCE 3: Empty Page", blocks[2])
        self.assertIn("STATUS: FAILED (PARTIAL)", blocks[2])
        self.assertIn("EXTRACTED CONTENT: None", blocks[2])

        self.assertIn("SOURCE 4: Restricted Portal", blocks[3])
        self.assertIn("STATUS: FAILED (BLOCKED)", blocks[3])
        self.assertIn("EXTRACTED CONTENT: None", blocks[3])

    def test_analyze_with_gemini_filters_usable_sources(self):
        """Test that analyze_with_gemini accurately counts accessible sources based on usable content."""
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
        self.assertEqual(res_empty["evidence_findings"][0]["evidence_status"], "INSUFFICIENT_EVIDENCE")


class TestEvidenceBackedFindings(unittest.TestCase):

    def setUp(self):
        self.sources = [
            {
                "url": "https://alpha.example.com/pricing/",
                "title": "Alpha Cloud",
                "status": "SUCCESS",
                "content_text": (
                    "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth. "
                    "All plans include automated TLS certificates and HTTP/2 routing."
                ),
                "headings": ["Starter Pricing", "Security Features"],
                "key_snippets": ["Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth."],
            },
            {
                "url": "https://beta.example.com/docs",
                "title": "Beta Host",
                "status": "SUCCESS",
                "content_text": (
                    "Beta Host provides container deployment and automated TLS certificates out of the box. "
                    "Enterprise contracts include custom throughput guarantees."
                ),
                "headings": ["Deployment", "Enterprise"],
                "key_snippets": ["Beta Host provides container deployment and automated TLS certificates out of the box."],
            },
            {
                "url": "https://gamma.example.com/partial",
                "title": "Gamma Edge",
                "status": "PARTIAL",
                "content_text": "Gamma Edge runs serverless functions across 35 global edge regions.",
                "headings": ["Edge Network"],
                "key_snippets": ["Gamma Edge runs serverless functions across 35 global edge regions."],
                "error_message": "Navigation timed out after 15s, partial DOM captured.",
            },
        ]

    def test_supported_findings_contain_valid_excerpts_and_canonical_urls(self):
        """Supported findings returned by Gemini retain verified verbatim excerpts and original source URLs."""
        mock_payload = {
            "research_summary": "Alpha Cloud lists a $19/month Starter tier.",
            "evidence_findings": [
                {
                    "finding": "Alpha Cloud's Starter tier costs $19 per month and includes 100GB bandwidth.",
                    "supporting_sources": [
                        {
                            "source_url": "https://alpha.example.com/pricing",  # Missing trailing slash
                            "source_title": "Alpha Cloud",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                            "source_status": "SUCCESS",
                        }
                    ],
                    "source_urls": ["https://alpha.example.com/pricing"],
                    "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                    "inference_basis": "",
                    "limitation_note": "",
                }
            ],
            "source_findings": [
                {
                    "source_title": "Alpha Cloud",
                    "source_url": "https://alpha.example.com/pricing",
                    "source_status": "SUCCESS",
                    "key_findings": ["Starter tier priced at $19/month with 100GB bandwidth."],
                    "evidence_snippets": ["Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth."],
                }
            ],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Alpha Cloud has transparent entry pricing.",
                "reasoning": "Pricing is explicitly stated.",
                "top_choice_or_conclusion": "Alpha Cloud",
                "supporting_sources": ["https://alpha.example.com/pricing/"],
            },
            "limitations": [],
        }

        with patch("google.genai.Client", return_value=_mock_genai_response(mock_payload)):
            report = analyze_with_gemini(
                query="Compare cloud pricing",
                sources=self.sources,
                api_key="fake-test-key"
            )

        self.assertFalse(report.get("error"))
        self.assertEqual(len(report["evidence_findings"]), 1)
        ef = report["evidence_findings"][0]
        self.assertEqual(ef["evidence_status"], "SUPPORTED")
        self.assertFalse(ef["is_inference"])
        # Original canonical URL (with trailing slash) preserved
        self.assertEqual(ef["source_urls"], ["https://alpha.example.com/pricing/"])
        self.assertEqual(ef["supporting_sources"][0]["source_url"], "https://alpha.example.com/pricing/")
        self.assertTrue(ef["supporting_sources"][0]["excerpt_verified"])
        self.assertIn("$19 per month with 100GB bandwidth", ef["evidence_excerpt"])
        self.assertTrue(verify_excerpt_in_source(ef["evidence_excerpt"], self.sources[0]))

    def test_cross_source_misattribution_and_fabricated_excerpts_rejected(self):
        """Excerpts belonging to a different site or fabricated entirely are rejected and marked UNSUPPORTED."""
        mock_payload = {
            "research_summary": "Mixed findings.",
            "evidence_findings": [
                {
                    # Claim misattributes Beta Host quote to Alpha Cloud!
                    "finding": "Alpha Cloud provides container deployment and custom throughput guarantees.",
                    "supporting_sources": [
                        {
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Beta Host provides container deployment and automated TLS certificates out of the box.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # Fabricated quote not present in ANY source!
                    "finding": "Beta Host costs $499 per month.",
                    "supporting_sources": [
                        {
                            "source_url": "https://beta.example.com/docs",
                            "evidence_excerpt": "Beta Host Starter package costs $499 per month forever.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
            ],
            "source_findings": [
                {
                    "source_title": "Alpha Cloud",
                    "source_url": "https://alpha.example.com/pricing/",
                    "key_findings": ["Offers $19/month Starter tier."],
                    "evidence_snippets": [
                        "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        "Completely invented quote from nowhere.",
                    ],
                }
            ],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Inconclusive",
                "reasoning": "Missing comparable pricing.",
                "top_choice_or_conclusion": "Inconclusive",
                "supporting_sources": [],
            },
            "limitations": [],
        }

        grounded = verify_and_ground_report(mock_payload, self.sources)

        f1, f2 = grounded["evidence_findings"]
        self.assertEqual(f1["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f1["supporting_sources"], [])
        self.assertEqual(f1["evidence_excerpt"], "")
        self.assertIn("Misattributed excerpt removed", f1["limitation_note"])

        self.assertEqual(f2["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f2["supporting_sources"], [])
        self.assertEqual(f2["evidence_excerpt"], "")
        self.assertIn("Unverified excerpt removed", f2["limitation_note"])

        # Source finding keeps only the verified snippet and removes fabricated one
        sf_snips = grounded["source_findings"][0]["evidence_snippets"]
        self.assertEqual(len(sf_snips), 1)
        self.assertIn("Starter tier at $19 per month", sf_snips[0])

    def test_inferences_distinguished_from_directly_supported_claims(self):
        """Inferences carry is_inference=True, evidence_status='INFERENCE', and verified supporting citations."""
        mock_payload = {
            "research_summary": "Alpha provides clear entry pricing while Beta focuses on enterprise.",
            "evidence_findings": [
                {
                    "finding": "Alpha Cloud states its Starter plan costs $19/month.",
                    "supporting_sources": [
                        {
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    "finding": "Alpha Cloud appears easier to budget upfront for small projects than Beta Host.",
                    "supporting_sources": [
                        {
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        },
                        {
                            "source_url": "https://beta.example.com/docs",
                            "evidence_excerpt": "Enterprise contracts include custom throughput guarantees.",
                        },
                    ],
                    "evidence_status": "SUPPORTED",  # Even if LLM sets SUPPORTED, is_inference=True promotes to INFERENCE!
                    "is_inference": True,
                    "inference_basis": "Alpha advertises a fixed $19/month tier whereas Beta describes custom enterprise contracts without public pricing in extracted text.",
                },
                {
                    # Ungrounded inference with no real excerpt must be marked UNSUPPORTED
                    "finding": "Gamma Edge is more expensive than Alpha Cloud.",
                    "supporting_sources": [
                        {
                            "source_url": "https://gamma.example.com/partial",
                            "evidence_excerpt": "Gamma Edge starts at $500 monthly.",  # Not in Gamma!
                        }
                    ],
                    "evidence_status": "INFERENCE",
                    "is_inference": True,
                    "inference_basis": "Claimed price difference.",
                },
            ],
            "source_findings": [],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Alpha Cloud for transparent pricing.",
                "reasoning": "Fixed public tier observed.",
                "top_choice_or_conclusion": "Alpha Cloud",
                "supporting_sources": ["https://alpha.example.com/pricing/"],
            },
            "limitations": [],
        }

        grounded = verify_and_ground_report(mock_payload, self.sources)
        direct, valid_inf, invalid_inf = grounded["evidence_findings"]

        self.assertFalse(direct["is_inference"])
        self.assertEqual(direct["evidence_status"], "SUPPORTED")

        self.assertTrue(valid_inf["is_inference"])
        self.assertEqual(valid_inf["evidence_status"], "INFERENCE")
        self.assertEqual(len(valid_inf["supporting_sources"]), 2)
        self.assertTrue(valid_inf["inference_basis"])

        self.assertTrue(invalid_inf["is_inference"])
        self.assertEqual(invalid_inf["evidence_status"], "UNSUPPORTED")
        self.assertEqual(invalid_inf["supporting_sources"], [])

    def test_multiple_supporting_sources_handled_correctly(self):
        """A single finding supported by multiple sources preserves each URL with its own verbatim excerpt."""
        mock_payload = {
            "research_summary": "Both Alpha Cloud and Beta Host include automated TLS certificates.",
            "evidence_findings": [
                {
                    "finding": "Both Alpha Cloud and Beta Host include automated TLS certificates.",
                    "supporting_sources": [
                        {
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "All plans include automated TLS certificates and HTTP/2 routing.",
                        },
                        {
                            "source_url": "https://beta.example.com/docs",
                            "evidence_excerpt": "Beta Host provides container deployment and automated TLS certificates out of the box.",
                        },
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                }
            ],
            "source_findings": [],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Both offer automated TLS.",
                "reasoning": "Directly documented on both sites.",
                "top_choice_or_conclusion": "Tie",
                "supporting_sources": ["https://alpha.example.com/pricing/", "https://beta.example.com/docs"],
            },
            "limitations": [],
        }

        grounded = verify_and_ground_report(mock_payload, self.sources)
        ef = grounded["evidence_findings"][0]
        self.assertEqual(ef["evidence_status"], "SUPPORTED")
        self.assertEqual(ef["source_urls"], ["https://alpha.example.com/pricing/", "https://beta.example.com/docs"])
        self.assertEqual(len(ef["supporting_sources"]), 2)
        self.assertEqual(ef["supporting_sources"][0]["source_title"], "Alpha Cloud")
        self.assertEqual(ef["supporting_sources"][1]["source_title"], "Beta Host")
        self.assertIn("HTTP/2 routing", ef["supporting_sources"][0]["evidence_excerpt"])
        self.assertIn("container deployment", ef["supporting_sources"][1]["evidence_excerpt"])

    def test_partial_sources_retain_partial_status_across_findings(self):
        """Findings backed solely by PARTIAL sources retain PARTIAL source_status and PARTIALLY_SUPPORTED status."""
        mock_payload = {
            "research_summary": "Gamma Edge operates across 35 global edge regions.",
            "evidence_findings": [
                {
                    "finding": "Gamma Edge runs serverless functions across 35 global edge regions.",
                    "supporting_sources": [
                        {
                            "source_url": "https://gamma.example.com/partial",
                            "evidence_excerpt": "Gamma Edge runs serverless functions across 35 global edge regions.",
                            "source_status": "SUCCESS",  # Incorrectly claimed SUCCESS by LLM; verifier must fix!
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                }
            ],
            "source_findings": [
                {
                    "source_title": "Gamma Edge",
                    "source_url": "https://gamma.example.com/partial",
                    "source_status": "SUCCESS",
                    "key_findings": ["Serverless across 35 edge regions."],
                    "evidence_snippets": ["Gamma Edge runs serverless functions across 35 global edge regions."],
                }
            ],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Gamma covers 35 regions based on partial extraction.",
                "reasoning": "Observed in partially scraped DOM.",
                "top_choice_or_conclusion": "Gamma Edge",
                "supporting_sources": ["https://gamma.example.com/partial"],
            },
            "limitations": [],
        }

        grounded = verify_and_ground_report(mock_payload, self.sources)
        ef = grounded["evidence_findings"][0]
        self.assertEqual(ef["supporting_sources"][0]["source_status"], "PARTIAL")
        self.assertEqual(ef["evidence_status"], "PARTIALLY_SUPPORTED")
        self.assertIn("partial", ef["limitation_note"].lower())

        sf = grounded["source_findings"][0]
        self.assertEqual(sf["source_status"], "PARTIAL")
        self.assertTrue(any("partial" in lim.lower() for lim in grounded["limitations"]))

    def test_missing_evidence_does_not_fabricate_claims(self):
        """When sources contain unrelated content or insufficient evidence, gap is reported honestly."""
        irrelevant_sources = [
            {
                "url": "https://alpha.example.com/pricing/",
                "title": "Alpha Cloud",
                "status": "SUCCESS",
                "content_text": "Welcome to Alpha Cloud. Check our blog for company culture updates.",
                "headings": ["Blog"],
                "key_snippets": ["Welcome to Alpha Cloud. Check our blog for company culture updates."],
            }
        ]
        mock_payload = {
            "research_summary": "Extracted content did not report HIPAA compliance or SOC2 certification.",
            "evidence_findings": [
                {
                    "finding": "Neither HIPAA compliance nor SOC2 certification was reported in Alpha Cloud's extracted content.",
                    "supporting_sources": [],
                    "source_urls": ["https://alpha.example.com/pricing/"],
                    "evidence_excerpt": "",
                    "evidence_status": "INSUFFICIENT_EVIDENCE",
                    "is_inference": False,
                    "limitation_note": "Extracted text only discussed company culture; compliance documentation was absent (does not prove absence on other pages).",
                }
            ],
            "source_findings": [
                {
                    "source_title": "Alpha Cloud",
                    "source_url": "https://alpha.example.com/pricing/",
                    "source_status": "SUCCESS",
                    "key_findings": ["Insufficient evidence: source content had no compliance information."],
                    "evidence_snippets": [],
                }
            ],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Inconclusive due to missing compliance details.",
                "reasoning": "Compliance info absent from extracted pages.",
                "top_choice_or_conclusion": "Inconclusive",
                "supporting_sources": [],
            },
            "limitations": ["No relevant evidence found for HIPAA or SOC2."],
        }

        with patch("google.genai.Client", return_value=_mock_genai_response(mock_payload)):
            report = analyze_with_gemini(
                query="Verify HIPAA and SOC2 certifications",
                sources=irrelevant_sources,
                api_key="fake-key"
            )

        ef = report["evidence_findings"][0]
        self.assertEqual(ef["evidence_status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(ef["supporting_sources"], [])
        self.assertEqual(ef["source_urls"], [])
        self.assertEqual(ef["evidence_excerpt"], "")
        self.assertIn("company culture", ef["limitation_note"])

    def test_fallback_heuristics_produce_grounded_evidence_findings(self):
        """Offline/fallback mode builds verified evidence_findings and retains PARTIAL status."""
        report = generate_local_heuristic_report("Compare cloud hosting", self.sources, missing_api_key=True)
        self.assertFalse(report.get("error"))
        self.assertGreaterEqual(len(report["evidence_findings"]), 3)

        # Validate entire fallback payload through Pydantic model cleanly
        validated = StructuredResearchReport(**report)
        gamma_findings = [
            ef for ef in validated.evidence_findings
            if "https://gamma.example.com/partial" in ef.source_urls
        ]
        self.assertTrue(gamma_findings)
        self.assertEqual(gamma_findings[0].evidence_status, "PARTIALLY_SUPPORTED")
        self.assertEqual(gamma_findings[0].supporting_sources[0].source_status, "PARTIAL")

    def test_existing_report_generation_and_schema_compatibility(self):
        """Legacy schema, markdown export, and mocked ResearchSession pipeline all work seamlessly."""
        # 1. Backward compatibility with legacy schema (no evidence_findings/source_status fields)
        legacy_payload = {
            "research_summary": "Summary text",
            "source_findings": [
                {
                    "source_title": "Alpha Cloud",
                    "source_url": "https://alpha.example.com/pricing/",
                    "key_findings": ["Starter tier at $19"],
                    "evidence_snippets": ["Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth."],
                }
            ],
            "comparison_matrix": [
                {
                    "criterion": "Pricing",
                    "source_evaluations": {"Alpha Cloud": "$19/month"},
                    "synthesis_note": "Entry pricing verified.",
                }
            ],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Alpha Cloud",
                "reasoning": "Clear pricing.",
                "top_choice_or_conclusion": "Alpha Cloud",
                "supporting_sources": ["https://alpha.example.com/pricing/"],
            },
            "limitations": [],
        }
        legacy_validated = StructuredResearchReport(**legacy_payload)
        self.assertEqual(legacy_validated.evidence_findings, [])

        # 2. Mocked end-to-end ResearchSession (zero network / zero live Gemini calls)
        s1 = ScrapedSource("https://alpha.example.com/pricing/")
        s1.title = "Alpha Cloud"
        s1.status = "SUCCESS"
        s1.content_text = self.sources[0]["content_text"]
        s1.headings = self.sources[0]["headings"]
        s1.key_snippets = self.sources[0]["key_snippets"]
        s1.character_count = len(s1.content_text)

        s2 = ScrapedSource("https://gamma.example.com/partial")
        s2.title = "Gamma Edge"
        s2.status = "PARTIAL"
        s2.content_text = self.sources[2]["content_text"]
        s2.headings = self.sources[2]["headings"]
        s2.key_snippets = self.sources[2]["key_snippets"]
        s2.error_message = "Timed out after 15s"
        s2.character_count = len(s2.content_text)

        mock_ai_json = {
            "research_summary": "Alpha offers a $19 tier while Gamma reports 35 edge regions (partial).",
            "evidence_findings": [
                {
                    "finding": "Alpha Cloud Starter tier costs $19/month.",
                    "supporting_sources": [
                        {
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    "finding": "Gamma Edge serves serverless functions across 35 global edge regions.",
                    "supporting_sources": [
                        {
                            "source_url": "https://gamma.example.com/partial",
                            "evidence_excerpt": "Gamma Edge runs serverless functions across 35 global edge regions.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
            ],
            "source_findings": [
                {
                    "source_title": "Alpha Cloud",
                    "source_url": "https://alpha.example.com/pricing/",
                    "key_findings": ["Starter tier is $19 per month."],
                    "evidence_snippets": ["Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth."],
                },
                {
                    "source_title": "Gamma Edge",
                    "source_url": "https://gamma.example.com/partial",
                    "key_findings": ["Runs across 35 global edge regions."],
                    "evidence_snippets": ["Gamma Edge runs serverless functions across 35 global edge regions."],
                },
            ],
            "comparison_matrix": [
                {
                    "criterion": "Coverage",
                    "source_evaluations": {"Alpha Cloud": "100GB Starter", "Gamma Edge": "35 edge regions"},
                    "synthesis_note": "Different focus areas reported.",
                }
            ],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Choose Alpha Cloud for predictable pricing.",
                "reasoning": "Verified pricing details.",
                "top_choice_or_conclusion": "Alpha Cloud",
                "supporting_sources": ["https://alpha.example.com/pricing/"],
            },
            "limitations": [],
        }

        with (
            patch("analyzer.validate_research_inputs", return_value=(True, [])),
            patch("analyzer.scrape_multiple_urls", return_value=[s1, s2]),
            patch("google.genai.Client", return_value=_mock_genai_response(mock_ai_json)),
            patch("analyzer.time.sleep", return_value=None),
        ):
            session = ResearchSession(
                query="Compare Alpha Cloud and Gamma Edge",
                urls=["https://alpha.example.com/pricing/", "https://gamma.example.com/partial"],
                api_key="fake-key",
            )
            final_report = session.execute()

        self.assertIn("evidence_findings", final_report)
        self.assertEqual(len(final_report["evidence_findings"]), 2)
        self.assertEqual(final_report["evidence_findings"][1]["evidence_status"], "PARTIALLY_SUPPORTED")
        self.assertIn("markdown_content", final_report)
        self.assertIn("Evidence-Backed Findings & Traceability", final_report["markdown_content"])
        self.assertIn("PARTIALLY_SUPPORTED", final_report["markdown_content"])

        # Legacy generate_markdown_report direct call still succeeds
        legacy_md = generate_markdown_report({
            "query": "Legacy test",
            "summary": "Overview",
            "recommendation": "Use A",
            "sources": [{"title": "Site A", "url": "https://a.com", "status": "SUCCESS", "key_findings": ["Fast"]}],
            "comparison": [{"criterion": "Speed", "details": "10ms", "evaluation": "Fast"}],
        })
        self.assertIn("# WebScout Intelligence Report: Legacy test", legacy_md)
        self.assertIn("| **Speed** | 10ms | Fast |", legacy_md)

    def test_partial_multi_source_verification_and_fallback_synthesis(self):
        """Mixed valid/invalid citations and omitted evidence_findings are verified deterministically."""
        # Case A: 2 cited sources where Alpha verifies the TLS claim and Gamma's quote is fabricated -> PARTIALLY_SUPPORTED
        payload_mixed = {
            "research_summary": "TLS supported with partial corroboration.",
            "evidence_findings": [
                {
                    "finding": "Both services include automated TLS certificates.",
                    "supporting_sources": [
                        {
                            "source_id": "source_1",
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "All plans include automated TLS certificates and HTTP/2 routing.",
                        },
                        {
                            "source_id": "source_3",
                            "source_url": "https://gamma.example.com/partial",
                            "evidence_excerpt": "Automated TLS certificates provisioned on all 35 regions.",  # Fabricated
                        },
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # Mixed SUCCESS + PARTIAL verified citations retain PARTIAL metadata on Gamma
                    "finding": "Alpha uses HTTP/2 routing while Gamma operates across 35 edge regions.",
                    "supporting_sources": [
                        {
                            "source_id": "source_1",
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "All plans include automated TLS certificates and HTTP/2 routing.",
                        },
                        {
                            "source_id": "source_3",
                            "source_url": "https://gamma.example.com/partial",
                            "evidence_excerpt": "Gamma Edge runs serverless functions across 35 global edge regions.",
                        },
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
            ],
            "source_findings": [],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Alpha verified.",
                "reasoning": "Verified excerpt.",
                "top_choice_or_conclusion": "Alpha Cloud",
                "supporting_sources": ["https://alpha.example.com/pricing/"],
            },
            "limitations": [],
        }

        grounded_mixed = verify_and_ground_report(payload_mixed, self.sources)
        f_partial, f_success_plus_partial = grounded_mixed["evidence_findings"]

        self.assertEqual(f_partial["evidence_status"], "PARTIALLY_SUPPORTED")
        self.assertEqual(f_partial["verification_status"], "PARTIALLY_VERIFIED")
        self.assertEqual(f_partial["source_urls"], ["https://alpha.example.com/pricing/"])
        self.assertEqual(len(f_partial["supporting_sources"]), 1)
        self.assertEqual(len(f_partial["invalid_citations"]), 1)
        self.assertEqual(f_partial["invalid_citations"][0]["verification_error"], "excerpt_not_found")
        self.assertIn("Unverified excerpt removed", f_partial["limitation_note"])

        self.assertEqual(f_success_plus_partial["evidence_status"], "SUPPORTED")
        self.assertEqual(f_success_plus_partial["verification_status"], "PARTIALLY_VERIFIED")
        statuses = {c["source_url"]: c["source_status"] for c in f_success_plus_partial["supporting_sources"]}
        self.assertEqual(statuses["https://alpha.example.com/pricing/"], "SUCCESS")
        self.assertEqual(statuses["https://gamma.example.com/partial"], "PARTIAL")
        self.assertIn("partially extracted", f_success_plus_partial["limitation_note"].lower())

        # Case B: Model omits evidence_findings; verify_and_ground_report synthesizes from source_findings
        payload_omitted = {
            "research_summary": "Synthesized fallback.",
            "source_findings": [
                {
                    "source_id": "source_3",
                    "source_title": "Gamma Edge",
                    "source_url": "https://gamma.example.com/partial",
                    "key_findings": ["Gamma Edge runs serverless functions across 35 global edge regions."],
                    "evidence_snippets": ["Gamma Edge runs serverless functions across 35 global edge regions."],
                }
            ],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Gamma Edge",
                "reasoning": "Observed edge coverage.",
                "top_choice_or_conclusion": "Gamma Edge",
                "supporting_sources": ["https://gamma.example.com/partial"],
            },
            "limitations": [],
        }
        grounded_omitted = verify_and_ground_report(payload_omitted, self.sources)
        self.assertEqual(len(grounded_omitted["evidence_findings"]), 1)
        synth_ef = grounded_omitted["evidence_findings"][0]
        self.assertEqual(synth_ef["evidence_status"], "PARTIALLY_SUPPORTED")
        self.assertEqual(synth_ef["verification_status"], "PARTIALLY_VERIFIED")
        self.assertEqual(synth_ef["supporting_sources"][0]["source_status"], "PARTIAL")
        self.assertTrue(synth_ef["supporting_sources"][0]["is_verified"])

    def test_citation_source_id_and_unsubmitted_url_validation(self):
        """Citations with unknown sources, unsubmitted URLs, or mismatched source_id/URL are rejected."""
        payload = {
            "research_summary": "Audit citation sources.",
            "evidence_findings": [
                {
                    "finding": "Alpha Cloud offers a Starter tier at $19 per month.",
                    "supporting_sources": [
                        {
                            "source_id": "source_1",
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # Unknown source_id
                    "finding": "Source 99 provides dedicated GPU instances.",
                    "supporting_sources": [
                        {
                            "source_id": "source_99",
                            "evidence_excerpt": "Dedicated GPU instances included.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # Fabricated / unsubmitted external URL
                    "finding": "External site claims Alpha won Best Cloud 2026.",
                    "supporting_sources": [
                        {
                            "source_url": "https://invented-review.example.org/best-cloud",
                            "evidence_excerpt": "Alpha won Best Cloud 2026.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # source_id points to source_2 (Beta) while URL points to source_1 (Alpha) -> mismatch
                    "finding": "Starter tier costs $19/month.",
                    "supporting_sources": [
                        {
                            "source_id": "source_2",
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
            ],
            "source_findings": [
                {
                    "source_id": "source_1",
                    "source_title": "Alpha Cloud",
                    "source_url": "https://alpha.example.com/pricing/",
                    "key_findings": ["Starter tier is $19/month."],
                    "evidence_snippets": ["Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth."],
                },
                {
                    # Hallucinated source entry must be excluded from verified source_findings
                    "source_title": "Hallucinated Cloud Blog",
                    "source_url": "https://invented-review.example.org/best-cloud",
                    "key_findings": ["Best Cloud winner."],
                    "evidence_snippets": ["Alpha won Best Cloud 2026."],
                },
            ],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Alpha Cloud recommended.",
                "reasoning": "Transparent starter pricing.",
                "top_choice_or_conclusion": "Alpha Cloud",
                "supporting_sources": [
                    "https://alpha.example.com/pricing",  # valid submitted URL (normalized back to canonical)
                    "https://invented-review.example.org/best-cloud",  # fabricated URL -> must be removed
                ],
            },
            "limitations": [],
        }

        grounded = verify_and_ground_report(payload, self.sources)
        f_valid, f_unknown_id, f_unsubmitted_url, f_mismatch = grounded["evidence_findings"]

        self.assertEqual(f_valid["verification_status"], "VERIFIED")
        self.assertEqual(f_valid["evidence_status"], "SUPPORTED")
        self.assertEqual(f_valid["supporting_sources"][0]["source_id"], "source_1")
        self.assertTrue(f_valid["supporting_sources"][0]["is_verified"])

        # Finding preserved, citation rejected cleanly
        self.assertEqual(f_unknown_id["finding"], "Source 99 provides dedicated GPU instances.")
        self.assertEqual(f_unknown_id["verification_status"], "UNVERIFIED")
        self.assertEqual(f_unknown_id["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f_unknown_id["supporting_sources"], [])
        self.assertEqual(f_unknown_id["invalid_citations"][0]["verification_error"], "unknown_source")

        self.assertEqual(f_unsubmitted_url["verification_status"], "UNVERIFIED")
        self.assertEqual(f_unsubmitted_url["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f_unsubmitted_url["supporting_sources"], [])
        self.assertEqual(f_unsubmitted_url["invalid_citations"][0]["verification_error"], "unsubmitted_url")

        self.assertEqual(f_mismatch["verification_status"], "UNVERIFIED")
        self.assertEqual(f_mismatch["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f_mismatch["invalid_citations"][0]["verification_error"], "source_id_mismatch")

        # Invented source_finding excluded; only submitted source_1 preserved
        self.assertEqual(len(grounded["source_findings"]), 1)
        self.assertEqual(grounded["source_findings"][0]["source_url"], "https://alpha.example.com/pricing/")
        self.assertEqual(grounded["source_findings"][0]["source_id"], "source_1")

        # Recommendation supporting_sources preserves canonical submitted URL and strips fabricated URL
        self.assertEqual(grounded["recommendation"]["supporting_sources"], ["https://alpha.example.com/pricing/"])
        self.assertTrue(any("invented-review.example.org" in lim for lim in grounded["limitations"]))

    def test_irrelevant_excerpt_and_numeric_mismatch_and_missing_citations(self):
        """Excerpts present on the page that do not support the claim, altered metrics, and uncited claims are rejected."""
        sources_with_boilerplate = [
            {
                "source_id": "source_1",
                "url": "https://alpha.example.com/pricing/",
                "title": "Alpha Cloud",
                "status": "SUCCESS",
                "content_text": (
                    "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth. "
                    "Alpha Cloud respects browser cookie preferences and privacy policy terms."
                ),
                "headings": ["Starter Pricing", "Privacy Policy"],
                "key_snippets": ["Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth."],
            }
        ]

        # Direct unit check of assess_citation_relevance on irrelevant boilerplate sharing brand tokens ("Alpha Cloud")
        is_rel, _ = assess_citation_relevance(
            finding_text="Alpha Cloud guarantees 99.99% enterprise SLA compliance.",
            excerpt="Alpha Cloud respects browser cookie preferences and privacy policy terms.",
            source=sources_with_boilerplate[0],
        )
        self.assertFalse(is_rel)

        mock_payload = {
            "research_summary": "Mixed quality AI assertions.",
            "evidence_findings": [
                {
                    # Verbatim quote from page, but completely irrelevant to SLA claim!
                    "finding": "Alpha Cloud guarantees 99.99% enterprise SLA compliance.",
                    "supporting_sources": [
                        {
                            "source_id": "source_1",
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud respects browser cookie preferences and privacy policy terms.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # Altered numeric price ($499 vs actual $19)
                    "finding": "Alpha Cloud Starter tier costs $499 per month with 100GB bandwidth.",
                    "supporting_sources": [
                        {
                            "source_id": "source_1",
                            "source_url": "https://alpha.example.com/pricing/",
                            "evidence_excerpt": "Alpha Cloud offers a Starter tier at $19 per month with 100GB bandwidth.",
                        }
                    ],
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
                {
                    # Claim with zero citations falsely marked SUPPORTED by AI
                    "finding": "Alpha Cloud operates data centers in Antarctica.",
                    "supporting_sources": [],
                    "evidence_excerpt": "",
                    "evidence_status": "SUPPORTED",
                    "is_inference": False,
                },
            ],
            "source_findings": [],
            "comparison_matrix": [],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Inconclusive",
                "reasoning": "Validation catches unverified claims.",
                "top_choice_or_conclusion": "Inconclusive",
                "supporting_sources": [],
            },
            "limitations": [],
        }

        with patch("google.genai.Client", return_value=_mock_genai_response(mock_payload)):
            report = analyze_with_gemini(
                query="Check Alpha SLA and Starter pricing",
                sources=sources_with_boilerplate,
                api_key="fake-key",
            )

        f_irrel, f_numeric, f_uncited = report["evidence_findings"]

        self.assertEqual(f_irrel["verification_status"], "UNVERIFIED")
        self.assertEqual(f_irrel["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f_irrel["supporting_sources"], [])
        self.assertEqual(f_irrel["evidence_excerpt"], "")
        self.assertEqual(f_irrel["invalid_citations"][0]["verification_error"], "irrelevant_excerpt")

        self.assertEqual(f_numeric["verification_status"], "UNVERIFIED")
        self.assertEqual(f_numeric["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f_numeric["supporting_sources"], [])
        self.assertEqual(f_numeric["invalid_citations"][0]["verification_error"], "numeric_mismatch")

        self.assertEqual(f_uncited["finding"], "Alpha Cloud operates data centers in Antarctica.")
        self.assertEqual(f_uncited["verification_status"], "UNVERIFIED")
        self.assertEqual(f_uncited["evidence_status"], "UNSUPPORTED")
        self.assertEqual(f_uncited["supporting_sources"], [])


class TestContradictionDetection(unittest.TestCase):

    def setUp(self):
        self.sources = [
            {
                "source_id": "source_1",
                "url": "https://site-one.example.com/product",
                "title": "Site One Review",
                "status": "SUCCESS",
                "content_text": (
                    "NovaCloud Starter plan costs ₹499 per month and includes a 30-day free trial with 1000 MB storage. "
                    "NovaCloud SDK v1.0 requires Python 3.8. "
                    "NovaBook Air was released in March 2024 and offers 18 hours battery life. "
                    "NovaCloud guarantees 99.9% uptime SLA."
                ),
            },
            {
                "source_id": "source_2",
                "url": "https://site-two.example.com/specs",
                "title": "Site Two Docs",
                "status": "SUCCESS",
                "content_text": (
                    "NovaCloud Starter plan is priced at ₹799 per month while the Pro plan costs ₹599 per month. "
                    "Signups receive a one-month free trial and 1 GB storage. "
                    "NovaCloud SDK v2.0 requires Python 3.11. "
                    "NovaBook Air launched in November 2024 with 18 hours battery life. "
                    "In our 2023 archive, NovaCloud Starter tier included 500 MB storage."
                ),
            },
            {
                "source_id": "source_3",
                "url": "https://site-three.example.com/bench",
                "title": "Site Three Bench",
                "status": "SUCCESS",
                "content_text": (
                    "Tested NovaBook Air lasted 10 hours battery life in continuous playback. "
                    "Updated 2026 notice: NovaCloud Starter limit is now 2 GB storage. "
                    "FastPay processing fee is 2.9% per transaction."
                ),
            },
            {
                "source_id": "source_4",
                "url": "https://site-four.example.com/partial",
                "title": "Site Four Partial",
                "status": "PARTIAL",
                "content_text": "FastPay processing fee is 2.5% per transaction.",
                "error_message": "Navigation timed out after 15s",
            },
        ]

    def _base_report_with_discrepancies(self, discrepancies):
        return {
            "research_summary": "Comparative analysis complete.",
            "evidence_findings": [],
            "source_findings": [],
            "comparison_matrix": [],
            "discrepancies": discrepancies,
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Review verified findings.",
                "reasoning": "Based on extracted sources.",
                "top_choice_or_conclusion": "Site One Review",
                "supporting_sources": ["https://site-one.example.com/product"],
            },
            "limitations": [],
        }

    def test_01_genuinely_conflicting_claims_confirmed(self):
        """Two conflicting claims about the exact same plan, period, currency, and subject verify as CONFIRMED_CONTRADICTION."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "NovaCloud Starter Plan Monthly Price",
                "subject": "NovaCloud Starter Plan",
                "attribute": "monthly price",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaCloud Starter plan costs ₹499 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan costs ₹499 per month",
                        "stance": "side_a",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "NovaCloud Starter plan costs ₹799 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan is priced at ₹799 per month",
                        "stance": "side_b",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "Both sources quote monthly INR pricing for the same NovaCloud Starter plan with conflicting amounts (₹499 vs ₹799).",
                "confidence": "HIGH",
            },
            {
                # Conflicting release date claims for the same product
                "criterion": "NovaBook Air Release Date",
                "subject": "NovaBook Air",
                "attribute": "release date",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaBook Air was released in March 2024.",
                        "evidence_excerpt": "NovaBook Air was released in March 2024",
                        "stance": "side_a",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "NovaBook Air launched in November 2024.",
                        "evidence_excerpt": "NovaBook Air launched in November 2024",
                        "stance": "side_b",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "Sources report conflicting launch months (March 2024 vs November 2024) for NovaBook Air.",
                "confidence": "HIGH",
            },
        ])

        with patch("google.genai.Client", return_value=_mock_genai_response(payload)):
            report = analyze_with_gemini("Compare NovaCloud pricing and release dates", self.sources, api_key="fake")

        self.assertEqual(len(report["discrepancies"]), 2)
        d1, d2 = report["discrepancies"]
        for d in (d1, d2):
            self.assertEqual(d["contradiction_status"], "CONFIRMED_CONTRADICTION")
            self.assertEqual(d["verification_status"], "VERIFIED")
            self.assertEqual(d["confidence"], "HIGH")
            self.assertEqual(len(d["supporting_sources"]), 2)
            self.assertTrue(all(c["is_verified"] for c in d["supporting_sources"]))

        self.assertEqual(d1["source_a_url"], "https://site-one.example.com/product")
        self.assertEqual(d1["source_b_url"], "https://site-two.example.com/specs")
        self.assertIn("₹499", d1["source_a_excerpt"])
        self.assertIn("₹799", d1["source_b_excerpt"])

    def test_02_equivalent_claims_expressed_differently_not_contradiction(self):
        """Equivalent expressions (30-day vs one-month trial, 1000 MB vs 1 GB) are classified NOT_A_CONTRADICTION."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "Trial Duration",
                "subject": "NovaCloud Starter Trial",
                "attribute": "trial duration",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "Includes a 30-day free trial.",
                        "evidence_excerpt": "includes a 30-day free trial",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "Provides a one-month free trial.",
                        "evidence_excerpt": "Signups receive a one-month free trial",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",  # LLM wrongly calls this a conflict; verifier corrects!
                "explanation": "30 days vs one month",
            },
            {
                "criterion": "Storage Allocation",
                "subject": "NovaCloud Starter",
                "attribute": "storage",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "Includes 1000 MB storage.",
                        "evidence_excerpt": "with 1000 MB storage.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "Includes 1 GB storage.",
                        "evidence_excerpt": "1 GB storage.",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "1000 MB vs 1 GB",
            },
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(grounded["discrepancies"], [])
        self.assertEqual(len(grounded["non_contradictory_differences"]), 2)
        for item in grounded["non_contradictory_differences"]:
            self.assertEqual(item["contradiction_status"], "NOT_A_CONTRADICTION")
            self.assertEqual(item["verification_status"], "VERIFIED")
            self.assertIn("Equivalent", item["explanation"])

    def test_03_different_plans_not_contradiction(self):
        """Different prices for different subscription plans (Starter ₹499 vs Pro ₹599) are NOT contradictions."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "Monthly Price",
                "subject": "NovaCloud Plans",
                "attribute": "price",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaCloud Starter plan costs ₹499 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan costs ₹499 per month",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "NovaCloud Pro plan costs ₹599 per month.",
                        "evidence_excerpt": "while the Pro plan costs ₹599 per month.",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "₹499/month vs ₹599/month",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(grounded["discrepancies"], [])
        self.assertEqual(len(grounded["non_contradictory_differences"]), 1)
        diff = grounded["non_contradictory_differences"][0]
        self.assertEqual(diff["contradiction_status"], "NOT_A_CONTRADICTION")
        self.assertIn("different subscription plans", diff["explanation"].lower())

    def test_04_different_product_versions_not_contradiction(self):
        """Differences across product versions (SDK v1.0 vs SDK v2.0) are classified NOT_A_CONTRADICTION."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "Minimum Python Version",
                "subject": "NovaCloud SDK",
                "attribute": "Python requirement",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaCloud SDK v1.0 requires Python 3.8.",
                        "evidence_excerpt": "NovaCloud SDK v1.0 requires Python 3.8.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "NovaCloud SDK v2.0 requires Python 3.11.",
                        "evidence_excerpt": "NovaCloud SDK v2.0 requires Python 3.11.",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "Python 3.8 vs 3.11",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(grounded["discrepancies"], [])
        self.assertEqual(len(grounded["non_contradictory_differences"]), 1)
        diff = grounded["non_contradictory_differences"][0]
        self.assertEqual(diff["contradiction_status"], "NOT_A_CONTRADICTION")
        self.assertIn("different product models or versions", diff["explanation"].lower())

    def test_05_different_publication_dates_not_contradiction(self):
        """Different publication dates / timeframes (2023 archive vs 2026 update) are NOT contradictions."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "Starter Storage Limit",
                "subject": "NovaCloud Starter",
                "attribute": "storage limit",
                "claims": [
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "In the 2023 archive, NovaCloud Starter tier included 500 MB storage.",
                        "evidence_excerpt": "In our 2023 archive, NovaCloud Starter tier included 500 MB storage.",
                    },
                    {
                        "source_id": "source_3",
                        "source_url": "https://site-three.example.com/bench",
                        "claim": "Updated 2026 notice states Starter limit is now 2 GB storage.",
                        "evidence_excerpt": "Updated 2026 notice: NovaCloud Starter limit is now 2 GB storage.",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "500 MB vs 2 GB storage limit",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(grounded["discrepancies"], [])
        self.assertEqual(len(grounded["non_contradictory_differences"]), 1)
        diff = grounded["non_contradictory_differences"][0]
        self.assertEqual(diff["contradiction_status"], "NOT_A_CONTRADICTION")
        self.assertIn("different publication dates or timeframes", diff["explanation"].lower())

    def test_06_missing_information_on_one_source_not_contradiction(self):
        """Information reported in one source and omitted in another is NOT a contradiction."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "Uptime SLA",
                "subject": "NovaCloud SLA",
                "attribute": "uptime SLA",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaCloud guarantees 99.9% uptime SLA.",
                        "evidence_excerpt": "NovaCloud guarantees 99.9% uptime SLA.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "SLA percentage is not reported in Site Two Docs.",
                        "evidence_excerpt": "",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "Site One states SLA whereas Site Two does not specify.",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(grounded["discrepancies"], [])
        self.assertEqual(len(grounded["non_contradictory_differences"]), 1)
        diff = grounded["non_contradictory_differences"][0]
        self.assertEqual(diff["contradiction_status"], "NOT_A_CONTRADICTION")

    def test_07_claims_with_insufficient_evidence_rejected_from_confirmed(self):
        """Contradiction claims lacking valid verified evidence on one or both sides are rejected."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "Starter Monthly Price",
                "subject": "NovaCloud Starter",
                "attribute": "monthly price",
                "claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaCloud Starter plan costs ₹499 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan costs ₹499 per month",
                    },
                    {
                        "source_id": "source_3",
                        "source_url": "https://site-three.example.com/bench",
                        "claim": "NovaCloud Starter plan costs ₹999 per month.",
                        "evidence_excerpt": "NovaCloud Starter costs ₹999 per month.",  # Fabricated! Not in Site Three
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "₹499 vs ₹999",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(grounded["discrepancies"], [])
        self.assertEqual(len(grounded["non_contradictory_differences"]), 1)
        rejected = grounded["non_contradictory_differences"][0]
        self.assertEqual(rejected["contradiction_status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(rejected["verification_status"], "UNVERIFIED")
        self.assertEqual(len(rejected["supporting_sources"]), 1)
        self.assertTrue(any("insufficient verified evidence" in lim.lower() for lim in grounded["limitations"]))

    def test_08_potential_discrepancy_when_partial_or_ambiguous_context(self):
        """Conflicting verified claims involving a PARTIAL source or ambiguous qualifier become POTENTIAL_DISCREPANCY."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "FastPay Transaction Fee",
                "subject": "FastPay",
                "attribute": "processing fee",
                "claims": [
                    {
                        "source_id": "source_3",
                        "source_url": "https://site-three.example.com/bench",
                        "claim": "FastPay processing fee is 2.9% per transaction.",
                        "evidence_excerpt": "FastPay processing fee is 2.9% per transaction.",
                    },
                    {
                        "source_id": "source_4",
                        "source_url": "https://site-four.example.com/partial",
                        "claim": "FastPay processing fee is 2.5% per transaction.",
                        "evidence_excerpt": "FastPay processing fee is 2.5% per transaction.",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "Sources report 2.9% vs 2.5% processing fee.",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(len(grounded["discrepancies"]), 1)
        pot = grounded["discrepancies"][0]
        self.assertEqual(pot["contradiction_status"], "POTENTIAL_DISCREPANCY")
        self.assertEqual(pot["verification_status"], "PARTIALLY_VERIFIED")
        self.assertEqual(pot["confidence"], "LOW")
        self.assertIn("PARTIAL", pot["resolution_status"].upper())

    def test_09_multiple_sources_agreeing_against_one_conflicting_source(self):
        """Consensus from 2 agreeing sources vs 1 conflicting source (regardless of order) verifies all 3 sides."""
        payload = self._base_report_with_discrepancies([
            {
                "criterion": "NovaBook Air Battery Life",
                "subject": "NovaBook Air",
                "attribute": "battery life",
                "claims": [
                    {
                        # Put the minority outlier FIRST to verify order-independent majority clustering
                        "source_id": "source_3",
                        "source_url": "https://site-three.example.com/bench",
                        "claim": "NovaBook Air lasted 10 hours battery life.",
                        "evidence_excerpt": "Tested NovaBook Air lasted 10 hours battery life in continuous playback.",
                        "stance": "outlier",
                    },
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/product",
                        "claim": "NovaBook Air offers 18 hours battery life.",
                        "evidence_excerpt": "offers 18 hours battery life.",
                        "stance": "consensus",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/specs",
                        "claim": "NovaBook Air offers 18 hours battery life.",
                        "evidence_excerpt": "with 18 hours battery life.",
                        "stance": "consensus",
                    },
                ],
                "contradiction_status": "CONFIRMED_CONTRADICTION",
                "explanation": "Site One and Site Two state 18 hours battery life whereas Site Three measured 10 hours.",
                "confidence": "HIGH",
            }
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        self.assertEqual(len(grounded["discrepancies"]), 1)
        disc = grounded["discrepancies"][0]
        self.assertEqual(disc["contradiction_status"], "CONFIRMED_CONTRADICTION")
        self.assertEqual(disc["verification_status"], "VERIFIED")
        self.assertEqual(disc["confidence"], "HIGH")
        self.assertEqual(len(disc["claims"]), 3)
        self.assertEqual(len(disc["supporting_sources"]), 3)
        self.assertEqual(len(disc["evidence_excerpts"]), 3)
        self.assertIn("Multiple sources", disc["explanation"])
        self.assertIn("https://site-one.example.com/product", disc["explanation"])
        self.assertIn("https://site-three.example.com/bench", disc["explanation"])

        # Also check markdown formatting preserves structured discrepancy citations cleanly
        md = generate_markdown_report({
            "query": "NovaBook Battery",
            "summary": "Summary",
            "recommendation": "Check battery reviews",
            "sources": self.sources[:3],
            "discrepancies": grounded["discrepancies"],
        })
        self.assertIn("CONFIRMED_CONTRADICTION | VERIFIED | Confidence: HIGH", md)
        self.assertIn("Tested NovaBook Air lasted 10 hours battery life", md)

    def test_10_heuristic_fallback_detects_real_conflicts_and_avoids_fake_coverage_discrepancies(self):
        """Heuristic mode avoids bogus Coverage Depth discrepancies and only surfaces verified quantitative conflicts."""
        non_conflicting_sources = [
            {
                "source_id": "source_1",
                "url": "https://a.example.com",
                "title": "Alpha",
                "status": "SUCCESS",
                "content_text": "Alpha Cloud offers automated deployments and built-in observability dashboards.",
                "headings": ["Overview"],
                "key_snippets": ["Alpha Cloud offers automated deployments and built-in observability dashboards."],
            },
            {
                "source_id": "source_2",
                "url": "https://b.example.com",
                "title": "Beta",
                "status": "SUCCESS",
                "content_text": "Beta Database focuses exclusively on distributed PostgreSQL storage with point-in-time recovery.",
                "headings": ["Storage"],
                "key_snippets": ["Beta Database focuses exclusively on distributed PostgreSQL storage with point-in-time recovery."],
            },
        ]
        rep_clean = generate_local_heuristic_report("Compare Alpha and Beta", non_conflicting_sources)
        self.assertEqual(rep_clean["discrepancies"], [])

        conflicting_sources = [
            {
                "source_id": "source_1",
                "url": "https://one.example.com",
                "title": "Source 1",
                "status": "SUCCESS",
                "content_text": "NovaCloud Starter tier monthly price is ₹499 per month.",
                "headings": ["Pricing"],
                "key_snippets": ["NovaCloud Starter tier monthly price is ₹499 per month."],
            },
            {
                "source_id": "source_2",
                "url": "https://two.example.com",
                "title": "Source 2",
                "status": "SUCCESS",
                "content_text": "NovaCloud Starter tier monthly price is ₹799 per month.",
                "headings": ["Pricing"],
                "key_snippets": ["NovaCloud Starter tier monthly price is ₹799 per month."],
            },
        ]
        rep_conflict = generate_local_heuristic_report("NovaCloud Starter pricing", conflicting_sources)
        self.assertEqual(len(rep_conflict["discrepancies"]), 1)
        disc = rep_conflict["discrepancies"][0]
        self.assertEqual(disc["verification_status"], "VERIFIED")
        self.assertIn("₹499", disc["source_a_excerpt"])
        self.assertIn("₹799", disc["source_b_excerpt"])


class TestInformationStatusClassification(unittest.TestCase):

    def setUp(self):
        self.sources = [
            {
                "source_id": "source_1",
                "url": "https://vendor-a.example.com/overview",
                "title": "Vendor A Docs",
                "status": "SUCCESS",
                "content_text": (
                    "AppX supports Android 14 and includes a 30-day free trial with 1000 MB storage. "
                    "NovaCloud Starter plan costs ₹499 per month. "
                    "NovaCloud SDK v1.0 requires Python 3.8. "
                    "AlphaCloud offers built-in CLI deployment. "
                    "We use essential cookies to improve website navigation."
                ),
                "headings": ["Android Support", "Pricing", "SDK"],
            },
            {
                "source_id": "source_2",
                "url": "https://vendor-b.example.com/specs",
                "title": "Vendor B Review",
                "status": "SUCCESS",
                "content_text": (
                    "AppX provides a one-month free trial with 1 GB storage. "
                    "NovaCloud Starter plan is priced at ₹799 per month, and Pro plan costs ₹599 per month. "
                    "NovaCloud SDK v2.0 requires Python 3.11. "
                    "BetaHost includes an interactive GUI dashboard. "
                    "In our 2023 archive, NovaCloud Starter tier included 500 MB storage. "
                    "AppX covers desktop workflows without mentioning mobile operating systems."
                ),
                "headings": ["Trial & Storage", "Plans"],
            },
            {
                "source_id": "source_3",
                "url": "https://vendor-c.example.com/partial",
                "title": "Vendor C Partial",
                "status": "PARTIAL",
                "content_text": "FastPay fee is 2.5% per transaction. AppX updated 2026 notice: Starter limit is 2 GB storage.",
                "headings": ["Fees"],
                "error_message": "Navigation timed out after 15s",
            },
            {
                "source_id": "source_4",
                "url": "https://vendor-d.example.com/failed",
                "title": "Vendor D Failed",
                "status": "TIMEOUT",
                "content_text": "",
                "error_message": "Timed out after 25s",
            },
        ]

    def _report_with_matrix(self, matrix_rows, discrepancies=None):
        return {
            "research_summary": "Classification synthesis.",
            "evidence_findings": [],
            "source_findings": [],
            "comparison_matrix": matrix_rows,
            "discrepancies": discrepancies or [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "See comparison details.",
                "reasoning": "Grounded in extracted sources.",
                "top_choice_or_conclusion": "Vendor A Docs",
                "supporting_sources": ["https://vendor-a.example.com/overview"],
            },
            "limitations": [],
        }

    def test_01_agreement_with_equivalent_wording(self):
        """Equivalent values expressed differently (30-day vs one-month trial, 1000 MB vs 1 GB) classify as AGREEMENT."""
        payload = self._report_with_matrix([
            {
                "criterion": "Trial Duration",
                "subject": "AppX Free Trial",
                "attribute": "trial duration",
                "classification": "CONTRADICTION",  # Deliberately wrong LLM label; verifier corrects!
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "Includes a 30-day free trial.",
                        "evidence_excerpt": "includes a 30-day free trial",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "Provides a one-month free trial.",
                        "evidence_excerpt": "AppX provides a one-month free trial",
                    },
                ],
            }
        ])
        grounded = verify_and_ground_report(payload, self.sources)
        row = grounded["comparison_matrix"][0]
        self.assertEqual(row["classification"], "AGREEMENT")
        self.assertEqual(row["verification_status"], "VERIFIED")
        self.assertEqual(row["confidence"], "HIGH")
        self.assertEqual(row["source_ids"], ["source_1", "source_2"])
        self.assertEqual(
            row["source_urls"],
            ["https://vendor-a.example.com/overview", "https://vendor-b.example.com/specs"],
        )
        self.assertEqual(len(row["supporting_evidence"]), 2)

    def test_02_explicit_contradiction_classified_correctly(self):
        """Genuine conflicting claims with verified evidence on both sides classify as CONTRADICTION."""
        payload = self._report_with_matrix([
            {
                "criterion": "NovaCloud Starter Monthly Price",
                "subject": "NovaCloud Starter Plan",
                "attribute": "monthly price",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "NovaCloud Starter plan costs ₹499 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan costs ₹499 per month.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "NovaCloud Starter plan is priced at ₹799 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan is priced at ₹799 per month",
                    },
                ],
            }
        ])
        grounded = verify_and_ground_report(payload, self.sources)
        row = grounded["comparison_matrix"][0]
        self.assertEqual(row["classification"], "CONTRADICTION")
        self.assertEqual(row["verification_status"], "VERIFIED")
        self.assertEqual(row["confidence"], "HIGH")
        self.assertEqual(len(row["supporting_evidence"]), 2)

    def test_03_missing_information_one_source_omits_never_contradiction(self):
        """A source omitting an attribute discussed elsewhere (e.g. Android support) classifies as MISSING_INFORMATION."""
        payload = self._report_with_matrix([
            {
                "criterion": "Android Support",
                "subject": "AppX",
                "attribute": "Android support",
                "classification": "CONTRADICTION",  # LLM misclassified omission as disagreement; verifier enforces!
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "AppX supports Android 14.",
                        "evidence_excerpt": "AppX supports Android 14",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "Android support is not mentioned in Vendor B Review.",
                        "evidence_excerpt": "",
                    },
                ],
            }
        ])
        grounded = verify_and_ground_report(payload, self.sources)
        row = grounded["comparison_matrix"][0]
        self.assertEqual(row["classification"], "MISSING_INFORMATION")
        self.assertEqual(grounded["discrepancies"], [])
        self.assertIn("absence of information", row["explanation"].lower())
        self.assertEqual(row["source_ids"], ["source_1", "source_2"])
        self.assertEqual(len(row["supporting_evidence"]), 1)

    def test_04_all_sources_omit_attribute_missing_information(self):
        """When all cleanly scraped sources omit a queried attribute, classify as MISSING_INFORMATION without fabricating."""
        payload = self._report_with_matrix([
            {
                "criterion": "HIPAA Compliance",
                "subject": "AppX",
                "attribute": "HIPAA compliance",
                "classification": "MISSING_INFORMATION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "HIPAA compliance is not reported in Vendor A Docs.",
                        "evidence_excerpt": "",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "Not specified in Vendor B Review.",
                        "evidence_excerpt": "",
                    },
                ],
            }
        ])
        grounded = verify_and_ground_report(payload, self.sources)
        row = grounded["comparison_matrix"][0]
        self.assertEqual(row["classification"], "MISSING_INFORMATION")
        self.assertEqual(row["supporting_evidence"], [])
        self.assertIn("absence of information", row["explanation"].lower())

    def test_05_not_comparable_versions_plans_dates_and_entities(self):
        """Different product versions, plans, outdated publication dates, and distinct products map to NOT_COMPARABLE."""
        payload = self._report_with_matrix([
            {
                "criterion": "Python Version Requirement",
                "subject": "NovaCloud SDK",
                "attribute": "Python version",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "NovaCloud SDK v1.0 requires Python 3.8.",
                        "evidence_excerpt": "NovaCloud SDK v1.0 requires Python 3.8.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "NovaCloud SDK v2.0 requires Python 3.11.",
                        "evidence_excerpt": "NovaCloud SDK v2.0 requires Python 3.11.",
                    },
                ],
            },
            {
                "criterion": "Plan Pricing",
                "subject": "NovaCloud",
                "attribute": "price",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "NovaCloud Starter plan costs ₹499 per month.",
                        "evidence_excerpt": "NovaCloud Starter plan costs ₹499 per month.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "Pro plan costs ₹599 per month.",
                        "evidence_excerpt": "and Pro plan costs ₹599 per month.",
                    },
                ],
            },
            {
                "criterion": "Starter Storage Allocation",
                "subject": "NovaCloud Starter",
                "attribute": "storage allocation",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "In the 2023 archive, NovaCloud Starter included 500 MB storage.",
                        "evidence_excerpt": "In our 2023 archive, NovaCloud Starter tier included 500 MB storage.",
                    },
                    {
                        "source_id": "source_3",
                        "source_url": "https://vendor-c.example.com/partial",
                        "claim": "Updated 2026 notice states Starter limit is 2 GB storage.",
                        "evidence_excerpt": "AppX updated 2026 notice: Starter limit is 2 GB storage.",
                    },
                ],
            },
            {
                "criterion": "Deployment Interface",
                "subject": "Platform Tooling",
                "attribute": "interface",
                "classification": "CONTRADICTION",
                "context_comparison": {"same_entity": False},
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "AlphaCloud offers built-in CLI deployment.",
                        "evidence_excerpt": "AlphaCloud offers built-in CLI deployment.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "BetaHost includes an interactive GUI dashboard.",
                        "evidence_excerpt": "BetaHost includes an interactive GUI dashboard.",
                    },
                ],
            },
        ])
        grounded = verify_and_ground_report(payload, self.sources)
        r_ver, r_plan, r_date, r_entity = grounded["comparison_matrix"]
        self.assertEqual(r_ver["classification"], "NOT_COMPARABLE")
        self.assertEqual(r_plan["classification"], "NOT_COMPARABLE")
        self.assertEqual(r_date["classification"], "NOT_COMPARABLE")
        self.assertEqual(r_entity["classification"], "NOT_COMPARABLE")

        # Validate alias normalization directly on ComparisonRow Pydantic model
        coerced = ComparisonRow(criterion="Test", classification="NON_COMPARABLE")
        self.assertEqual(coerced.classification, "NOT_COMPARABLE")
        coerced_agree = ComparisonRow(criterion="Test", classification="COMPATIBLE")
        self.assertEqual(coerced_agree.classification, "AGREEMENT")

    def test_06_insufficient_evidence_partial_failed_irrelevant_and_uncited(self):
        """Partial omission, failed source, irrelevant quotes, and uncited rows resolve to INSUFFICIENT_EVIDENCE."""
        payload = self._report_with_matrix([
            {
                # Partial capture omitting Android cannot prove MISSING_INFORMATION -> INSUFFICIENT_EVIDENCE
                "criterion": "Android Support (Partial Check)",
                "subject": "AppX",
                "attribute": "Android support",
                "classification": "MISSING_INFORMATION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "AppX supports Android 14.",
                        "evidence_excerpt": "AppX supports Android 14",
                    },
                    {
                        "source_id": "source_3",
                        "source_url": "https://vendor-c.example.com/partial",
                        "claim": "Android support is not mentioned.",
                        "evidence_excerpt": "",
                    },
                ],
            },
            {
                # Failed extraction source (TIMEOUT) -> INSUFFICIENT_EVIDENCE
                "criterion": "Fee Comparison (Failed Source)",
                "subject": "FastPay",
                "attribute": "fee",
                "classification": "MISSING_INFORMATION",
                "source_claims": [
                    {
                        "source_id": "source_3",
                        "source_url": "https://vendor-c.example.com/partial",
                        "claim": "FastPay fee is 2.5% per transaction.",
                        "evidence_excerpt": "FastPay fee is 2.5% per transaction.",
                    },
                    {
                        "source_id": "source_4",
                        "source_url": "https://vendor-d.example.com/failed",
                        "claim": "Source timed out.",
                        "evidence_excerpt": "",
                    },
                ],
            },
            {
                # Irrelevant cookie boilerplate quote cited for Security SLA -> INSUFFICIENT_EVIDENCE
                "criterion": "Enterprise SLA",
                "subject": "NovaCloud",
                "attribute": "uptime SLA",
                "classification": "AGREEMENT",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "NovaCloud guarantees 99.99% enterprise SLA.",
                        "evidence_excerpt": "We use essential cookies to improve website navigation.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "SLA 99.99% confirmed.",
                        "evidence_excerpt": "Completely invented SLA sentence.",
                    },
                ],
            },
            {
                # Zero evidence/claims while LLM asserts AGREEMENT -> forced INSUFFICIENT_EVIDENCE
                "criterion": "Uncited Row",
                "classification": "AGREEMENT",
                "source_claims": [],
                "source_evaluations": {},
                "synthesis_note": "Agreed without citations.",
            },
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        r_partial, r_failed, r_irrel, r_uncited = grounded["comparison_matrix"]
        for row in (r_partial, r_failed, r_irrel, r_uncited):
            self.assertEqual(row["classification"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(r_irrel["supporting_evidence"], [])
        self.assertEqual(len(r_irrel["invalid_citations"]), 2)
        self.assertEqual(r_uncited["verification_status"], "UNVERIFIED")

    def test_07_mocked_gemini_pipeline_and_heuristic_and_markdown_classifications(self):
        """Full mocked analyze_with_gemini, heuristic fallback, and Markdown export preserve classifications."""
        mock_payload = self._report_with_matrix([
            {
                "criterion": "Trial Duration",
                "subject": "AppX",
                "attribute": "free trial",
                "classification": "AGREEMENT",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://vendor-a.example.com/overview",
                        "claim": "Includes a 30-day free trial.",
                        "evidence_excerpt": "includes a 30-day free trial",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://vendor-b.example.com/specs",
                        "claim": "Provides a one-month free trial.",
                        "evidence_excerpt": "AppX provides a one-month free trial",
                    },
                ],
                "explanation": "Both sources confirm an equivalent 1-month / 30-day trial.",
            }
        ])

        with patch("google.genai.Client", return_value=_mock_genai_response(mock_payload)):
            report = analyze_with_gemini("Compare AppX trial", self.sources, api_key="fake-key")

        validated = StructuredResearchReport(**report)
        self.assertEqual(validated.comparison_matrix[0].classification, "AGREEMENT")

        md = generate_markdown_report({
            "query": "Compare AppX trial",
            "summary": "Trial summary",
            "recommendation": "Use AppX",
            "sources": self.sources[:2],
            "comparison": report["comparison_matrix"],
        })
        self.assertIn("`[AGREEMENT | VERIFIED]`", md)

        # Heuristic mode emits classified rows (no unverified claims marked AGREEMENT)
        heur_report = generate_local_heuristic_report("Compare pricing and Android support", self.sources)
        self.assertTrue(len(heur_report["comparison_matrix"]) >= 1)
        heur_validated = StructuredResearchReport(**heur_report)
        valid_classes = {"AGREEMENT", "CONTRADICTION", "MISSING_INFORMATION", "INSUFFICIENT_EVIDENCE", "NOT_COMPARABLE"}
        for cr in heur_validated.comparison_matrix:
            self.assertIn(cr.classification, valid_classes)


class TestComparisonMatrixUpgrade(unittest.TestCase):

    def setUp(self):
        self.sources = [
            {
                "source_id": "source_1",
                "url": "https://site-one.example.com/specs",
                "title": "TechSpec One",
                "status": "SUCCESS",
                "content_text": (
                    "UltraBook Pro comes with 1 TB SSD storage and a 1-year hardware warranty. "
                    "MacBook M2 model offers 18 hours battery life. "
                    "CloudPlan US tier costs $20 per month."
                ),
                "headings": ["Storage", "Battery Life", "Warranty"],
            },
            {
                "source_id": "source_2",
                "url": "https://site-two.example.com/review",
                "title": "Hardware Review Two",
                "status": "SUCCESS",
                "content_text": (
                    "UltraBook Pro includes 1024 GB SSD storage and provides 12 months warranty. "
                    "MacBook M3 model delivers 20 hours battery life. "
                    "CloudPlan India tier costs ₹1500 per month. "
                    "UltraBook Pro comes with 512 GB base SSD storage."
                ),
                "headings": ["Storage Capacity", "Pricing"],
            },
            {
                "source_id": "source_3",
                "url": "https://site-three.example.com/summary",
                "title": "Summary Blog Three",
                "status": "SUCCESS",
                "content_text": (
                    "UltraBook Pro highlights a bright OLED display and silent cooling."
                ),
                "headings": ["Display & Cooling"],
            },
            {
                "source_id": "source_4",
                "url": "https://site-four.example.com/partial",
                "title": "Partial Retail Four",
                "status": "PARTIAL",
                "content_text": "UltraBook Pro ships worldwide with USB-C fast charging.",
                "headings": ["Charging"],
                "error_message": "Timed out during page hydration",
            },
        ]

    def _mock_report(self, matrix_rows):
        return {
            "research_summary": "Attribute matrix comparison.",
            "evidence_findings": [],
            "source_findings": [],
            "comparison_matrix": matrix_rows,
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "Review attribute table.",
                "reasoning": "Based on verified source cells.",
                "top_choice_or_conclusion": "TechSpec One",
                "supporting_sources": ["https://site-one.example.com/specs"],
            },
            "limitations": [],
        }

    def test_01_two_and_three_source_structured_cells_and_missing_representation(self):
        """Comparison rows create structured per-source cells, representing missing attributes without inventing values."""
        payload = self._mock_report([
            {
                "criterion": "Warranty Coverage",
                "subject": "UltraBook Pro",
                "attribute": "warranty",
                "classification": "AGREEMENT",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "Includes a 1-year hardware warranty.",
                        "evidence_excerpt": "1-year hardware warranty",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "Provides 12 months warranty.",
                        "evidence_excerpt": "provides 12 months warranty",
                    },
                ],
            }
        ])

        # 2-source verification
        grounded_2 = verify_and_ground_report(payload, self.sources[:2])
        row_2 = grounded_2["comparison_matrix"][0]
        self.assertEqual(row_2["classification"], "AGREEMENT")
        self.assertEqual(set(row_2["cells"].keys()), {"source_1", "source_2"})
        for sid, expected_url in (
            ("source_1", "https://site-one.example.com/specs"),
            ("source_2", "https://site-two.example.com/review"),
        ):
            cell = row_2["cells"][sid]
            self.assertEqual(cell["source_id"], sid)
            self.assertEqual(cell["citation_url"], expected_url)
            self.assertEqual(cell["information_status"], "AGREEMENT")
            self.assertTrue(cell["is_verified"])
            self.assertTrue(cell["evidence_excerpt"])
            self.assertEqual(cell["normalized_value"], "12 months")

        # 3-source comparison where source_3 omits Warranty -> explicit MISSING_INFORMATION cell auto-represented!
        grounded_3 = verify_and_ground_report(payload, self.sources[:3])
        row_3 = grounded_3["comparison_matrix"][0]
        self.assertEqual(set(row_3["cells"].keys()), {"source_1", "source_2", "source_3"})
        self.assertEqual(row_3["cells"]["source_3"]["information_status"], "MISSING_INFORMATION")
        self.assertEqual(row_3["cells"]["source_3"]["extracted_value"], "Not reported in extracted content")
        self.assertEqual(row_3["cells"]["source_3"]["evidence_excerpt"], "")
        self.assertFalse(row_3["cells"]["source_3"]["is_verified"])

    def test_02_equivalent_storage_units_vs_different_storage_values(self):
        """1 TB == 1024 GB resolves to AGREEMENT, whereas 512 GB vs 1 TB remains CONTRADICTION."""
        payload = self._mock_report([
            {
                "criterion": "SSD Storage (1 TB vs 1024 GB)",
                "subject": "UltraBook Pro",
                "attribute": "storage",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "UltraBook Pro comes with 1 TB SSD storage.",
                        "evidence_excerpt": "UltraBook Pro comes with 1 TB SSD storage",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "UltraBook Pro includes 1024 GB SSD storage.",
                        "evidence_excerpt": "UltraBook Pro includes 1024 GB SSD storage",
                    },
                ],
            },
            {
                "criterion": "Base SSD Capacity (1 TB vs 512 GB)",
                "subject": "UltraBook Pro",
                "attribute": "SSD storage",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "UltraBook Pro comes with 1 TB SSD storage.",
                        "evidence_excerpt": "UltraBook Pro comes with 1 TB SSD storage",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "UltraBook Pro comes with 512 GB base SSD storage.",
                        "evidence_excerpt": "UltraBook Pro comes with 512 GB base SSD storage.",
                    },
                ],
            },
        ])

        grounded = verify_and_ground_report(payload, self.sources[:2])
        eq_row, diff_row = grounded["comparison_matrix"]

        self.assertEqual(eq_row["classification"], "AGREEMENT")
        self.assertEqual(eq_row["cells"]["source_1"]["normalized_value"], "1024 GB (IEC)")
        self.assertEqual(eq_row["cells"]["source_2"]["normalized_value"], "1024 GB (IEC)")

        self.assertEqual(diff_row["classification"], "CONTRADICTION")
        self.assertEqual(diff_row["cells"]["source_1"]["information_status"], "CONTRADICTION")
        self.assertEqual(diff_row["cells"]["source_2"]["information_status"], "CONTRADICTION")
        self.assertEqual(diff_row["cells"]["source_2"]["normalized_value"], "512 GB (IEC)")

    def test_03_different_currencies_and_product_versions_and_partial_sources(self):
        """Different currencies, different product versions (M2 vs M3), and partial captures classify properly."""
        payload = self._mock_report([
            {
                "criterion": "Monthly Pricing",
                "subject": "CloudPlan",
                "attribute": "price",
                "classification": "AGREEMENT",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "CloudPlan US tier costs $20 per month.",
                        "evidence_excerpt": "CloudPlan US tier costs $20 per month.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "CloudPlan India tier costs ₹1500 per month.",
                        "evidence_excerpt": "CloudPlan India tier costs ₹1500 per month.",
                    },
                ],
            },
            {
                "criterion": "Battery Life (M2 vs M3)",
                "subject": "MacBook",
                "attribute": "battery life",
                "classification": "CONTRADICTION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "MacBook M2 model offers 18 hours battery life.",
                        "evidence_excerpt": "MacBook M2 model offers 18 hours battery life.",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "MacBook M3 model delivers 20 hours battery life.",
                        "evidence_excerpt": "MacBook M3 model delivers 20 hours battery life.",
                    },
                ],
            },
            {
                "criterion": "Fast Charging Support",
                "subject": "UltraBook Pro",
                "attribute": "USB-C fast charging",
                "classification": "MISSING_INFORMATION",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "USB-C fast charging is not mentioned.",
                        "evidence_excerpt": "",
                    },
                    {
                        "source_id": "source_4",
                        "source_url": "https://site-four.example.com/partial",
                        "claim": "UltraBook Pro ships worldwide with USB-C fast charging.",
                        "evidence_excerpt": "UltraBook Pro ships worldwide with USB-C fast charging.",
                    },
                ],
            },
        ])

        grounded = verify_and_ground_report(payload, self.sources)
        curr_row, ver_row, partial_row = grounded["comparison_matrix"]

        self.assertEqual(curr_row["classification"], "NOT_COMPARABLE")
        self.assertEqual(curr_row["cells"]["source_1"]["normalized_value"], "USD 20")
        self.assertEqual(curr_row["cells"]["source_2"]["normalized_value"], "INR 1500")
        self.assertEqual(curr_row["cells"]["source_1"]["information_status"], "NOT_COMPARABLE")

        self.assertEqual(ver_row["classification"], "NOT_COMPARABLE")
        self.assertEqual(ver_row["cells"]["source_1"]["information_status"], "NOT_COMPARABLE")

        # Partial source cell keeps citation while marking partial extraction status cleanly
        self.assertEqual(partial_row["cells"]["source_4"]["citation_url"], "https://site-four.example.com/partial")
        self.assertTrue(partial_row["cells"]["source_4"]["is_verified"])
        self.assertEqual(partial_row["cells"]["source_1"]["information_status"], "MISSING_INFORMATION")

    def test_04_unsupported_values_and_repetitive_criteria_deduplication(self):
        """Fabricated/unsupported cell claims are rejected cleanly and repetitive criteria are deduplicated."""
        payload = self._mock_report([
            {
                "criterion": "Warranty",
                "subject": "UltraBook Pro",
                "attribute": "warranty",
                "classification": "AGREEMENT",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "Includes a 1-year hardware warranty.",
                        "evidence_excerpt": "1-year hardware warranty",
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "Provides 12 months warranty.",
                        "evidence_excerpt": "provides 12 months warranty",
                    },
                ],
            },
            {
                # Repetitive criterion name with no verified evidence -> deduplicated in favor of verified row above
                "criterion": "warranty",
                "classification": "AGREEMENT",
                "source_claims": [],
            },
            {
                # Unsupported fabricated excerpt
                "criterion": "GPU Boost Clock",
                "subject": "UltraBook Pro",
                "attribute": "GPU clock",
                "classification": "AGREEMENT",
                "source_claims": [
                    {
                        "source_id": "source_1",
                        "source_url": "https://site-one.example.com/specs",
                        "claim": "GPU reaches 2.4 GHz boost clock.",
                        "evidence_excerpt": "GPU reaches 2.4 GHz boost clock.",  # Fabricated
                    },
                    {
                        "source_id": "source_2",
                        "source_url": "https://site-two.example.com/review",
                        "claim": "Boost clock is 2400 MHz.",
                        "evidence_excerpt": "Boost clock is 2400 MHz.",  # Fabricated
                    },
                ],
            },
        ])

        grounded = verify_and_ground_report(payload, self.sources[:2])
        self.assertEqual(len(grounded["comparison_matrix"]), 2)
        warr_row, unsup_row = grounded["comparison_matrix"]
        self.assertEqual(warr_row["classification"], "AGREEMENT")
        self.assertEqual(unsup_row["classification"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(unsup_row["supporting_evidence"], [])
        self.assertEqual(unsup_row["cells"]["source_1"]["information_status"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(unsup_row["cells"]["source_1"]["is_verified"])

    def test_05_non_product_research_topic_mocked_and_dynamic_heuristic(self):
        """Comparison matrix adapts dynamically to non-product topics (climate policy) without hardcoded fields."""
        policy_sources = [
            {
                "source_id": "source_1",
                "url": "https://eu-climate.example.org/report",
                "title": "EU Policy Brief",
                "status": "SUCCESS",
                "content_text": (
                    "The EU Policy Brief sets an emission reduction target of 55% by 2030. "
                    "Verification relies on annual independent national audits."
                ),
                "headings": ["Emission Target", "Verification Mechanism"],
                "key_snippets": ["The EU Policy Brief sets an emission reduction target of 55% by 2030."],
            },
            {
                "source_id": "source_2",
                "url": "https://nordic-study.example.org/analysis",
                "title": "Nordic Climate Study",
                "status": "SUCCESS",
                "content_text": (
                    "The Nordic Climate Study reports an emission reduction target of 55% by 2030. "
                    "Implementation uses carbon border pricing audits."
                ),
                "headings": ["Emission Target", "Carbon Pricing"],
                "key_snippets": ["The Nordic Climate Study reports an emission reduction target of 55% by 2030."],
            },
            {
                "source_id": "source_3",
                "url": "https://unep-digest.example.org/global",
                "title": "UNEP Global Digest",
                "status": "SUCCESS",
                "content_text": (
                    "UNEP Global Digest summarizes forestry adaptation programs without specifying industrial reduction percentages."
                ),
                "headings": ["Forestry Adaptation"],
                "key_snippets": ["UNEP Global Digest summarizes forestry adaptation programs without specifying industrial reduction percentages."],
            },
        ]

        mock_payload = {
            "research_summary": "EU and Nordic sources align on a 55% 2030 reduction target while UNEP omits percentage targets.",
            "evidence_findings": [],
            "source_findings": [],
            "comparison_matrix": [
                {
                    "criterion": "2030 Emission Reduction Target",
                    "subject": "Climate Policy",
                    "attribute": "emission reduction target",
                    "classification": "AGREEMENT",
                    "source_claims": [
                        {
                            "source_id": "source_1",
                            "source_url": "https://eu-climate.example.org/report",
                            "claim": "Emission reduction target of 55% by 2030.",
                            "evidence_excerpt": "sets an emission reduction target of 55% by 2030.",
                        },
                        {
                            "source_id": "source_2",
                            "source_url": "https://nordic-study.example.org/analysis",
                            "claim": "Emission reduction target of 55% by 2030.",
                            "evidence_excerpt": "reports an emission reduction target of 55% by 2030.",
                        },
                        {
                            "source_id": "source_3",
                            "source_url": "https://unep-digest.example.org/global",
                            "claim": "Specific emission reduction percentage is not reported.",
                            "evidence_excerpt": "",
                        },
                    ],
                }
            ],
            "discrepancies": [],
            "pros_and_cons": [],
            "recommendation": {
                "verdict": "EU and Nordic documents specify a 55% target by 2030.",
                "reasoning": "Supported across two sources while UNEP focuses on forestry adaptation.",
                "top_choice_or_conclusion": "EU Policy Brief",
                "supporting_sources": ["https://eu-climate.example.org/report", "https://nordic-study.example.org/analysis"],
            },
            "limitations": [],
        }

        with patch("google.genai.Client", return_value=_mock_genai_response(mock_payload)):
            gemini_report = analyze_with_gemini(
                query="Compare climate frameworks on emission reduction target and verification mechanism",
                sources=policy_sources,
                preference="emission target, verification mechanism",
                api_key="fake-key",
            )

        validated = StructuredResearchReport(**gemini_report)
        row = validated.comparison_matrix[0]
        self.assertEqual(row.cells["source_1"].information_status, "MISSING_INFORMATION")
        self.assertEqual(row.cells["source_3"].information_status, "MISSING_INFORMATION")
        self.assertEqual(row.classification, "MISSING_INFORMATION")

        # Offline heuristic matrix derives climate policy attributes dynamically without hardware criteria
        heur = generate_local_heuristic_report(
            query="Compare climate policy studies",
            sources=policy_sources,
            preference="emission target, verification mechanism",
            missing_api_key=True,
        )
        criteria_names = [r["criterion"] for r in heur["comparison_matrix"]]
        self.assertTrue(any("emission target" in c.lower() for c in criteria_names))
        self.assertTrue(any("verification mechanism" in c.lower() for c in criteria_names))
        self.assertFalse(any(hw in " ".join(criteria_names).lower() for hw in ("processor", "ram", "battery", "display")))
        # Emission target appears cleanly in source_1 and source_2, omitted in source_3 -> source_3 cell marked MISSING_INFORMATION
        em_row = next(r for r in heur["comparison_matrix"] if "emission target" in r["criterion"].lower())
        self.assertTrue(em_row["cells"]["source_1"]["is_verified"])
        self.assertTrue(em_row["cells"]["source_2"]["is_verified"])
        self.assertEqual(em_row["cells"]["source_3"]["information_status"], "MISSING_INFORMATION")

        # Markdown export renders per-cell summary & statuses cleanly
        md = generate_markdown_report({
            "query": "Climate Policy Comparison",
            "summary": heur["research_summary"],
            "recommendation": heur["recommendation"]["verdict"],
            "sources": policy_sources,
            "comparison": heur["comparison_matrix"],
        })
        self.assertIn("MISSING_INFORMATION", md)


def _sample_report_payload(query: str, urls: list, tag: str) -> dict:
    """Builds a minimal deterministic ResearchSession.execute() return payload for UI tests."""
    return {
        "query": query,
        "preference": "",
        "summary": f"Executive Summary for {tag}: verified across inspected sources.",
        "recommendation": f"Choose option verified in {tag}.",
        "recommendation_detail": {
            "verdict": f"Choose option verified in {tag}.",
            "reasoning": f"Strongest verified evidence for {tag}.",
            "top_choice_or_conclusion": f"TopChoice-{tag}",
            "supporting_sources": list(urls),
        },
        "sources": [
            {
                "source_id": f"source_{i+1}",
                "url": u,
                "title": f"Source Title {tag} {i+1}",
                "status": "SUCCESS",
                "character_count": 450,
                "fetch_duration_seconds": 0.4,
                "key_snippets": [f"Verified snippet {tag} from site {i+1}."],
                "error_message": None,
            }
            for i, u in enumerate(urls)
        ],
        "source_findings": [
            {
                "source_id": f"source_{i+1}",
                "source_url": u,
                "source_title": f"Source Title {tag} {i+1}",
                "source_status": "SUCCESS",
                "key_findings": [f"Finding {tag} #{i+1}"],
                "evidence_snippets": [f"Verified snippet {tag} from site {i+1}."],
            }
            for i, u in enumerate(urls)
        ],
        "evidence_findings": [],
        "comparison": [
            {
                "criterion": f"Key Criterion ({tag})",
                "source_evaluations": {f"Site {i+1}": f"Value-{tag}-{i+1}" for i in range(len(urls))},
                "synthesis_note": f"Comparison note for {tag}.",
            }
        ],
        "discrepancies": [
            {
                "criterion": f"Conflict {tag}",
                "description": f"Discrepancy detail for {tag}.",
                "conflicting_sources": [u for u in urls[:2]],
                "resolution_status": "Confirmed Conflict",
            }
        ],
        "pros_and_cons": [
            {
                "source_name": f"Source Title {tag} 1",
                "advantages": [f"Pro {tag}"],
                "disadvantages": [f"Con {tag}"],
            }
        ],
        "limitations": [f"Limitation note {tag}"],
        "is_fallback": True,
        "model_used": "Built-in Heuristics",
        "elapsed_seconds": 0.5,
        "markdown_content": f"# WebScout Report {tag}\nSummary {tag}",
    }


class TestAppNewResearchAndResetWorkflow(unittest.TestCase):
    """End-to-end mocked Streamlit AppTest suite for New Research, Reset, and Session State isolation."""

    def setUp(self):
        self._orig_api_key = os.environ.get("GEMINI_API_KEY")
        os.environ.pop("GEMINI_API_KEY", None)

    def tearDown(self):
        if self._orig_api_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = self._orig_api_key

    def _mock_dns(self):
        import socket as _socket
        orig_resolve = _socket.gethostbyname

        def _fake_resolve(host: str) -> str:
            if ".example." in (host or "").lower():
                return "93.184.216.34"
            return orig_resolve(host)

        return patch("utils.socket.gethostbyname", side_effect=_fake_resolve)

    def _find_button(self, at, key: str):
        return next(b for b in at.button if b.key == key)

    def _find_text_input(self, at, key: str):
        return next(t for t in at.text_input if t.key == key)

    def _run_mocked_session(self, at, query: str, preference: str, urls: list, tag: str, mock_cls):
        mock_instance = MagicMock()
        mock_instance.execute.return_value = _sample_report_payload(query, urls, tag)
        mock_cls.return_value = mock_instance

        while len(at.session_state["urls_input"]) < len(urls):
            self._find_button(at, "add_url_btn").click().run()

        self._find_text_input(at, "query_input").input(query).run()
        self._find_text_input(at, "preference_input").input(preference).run()
        for idx, url in enumerate(urls):
            self._find_text_input(at, f"url_field_{idx}").input(url).run()

        self._find_button(at, "start_research_btn").click().run()

    def test_01_new_research_clears_results_inputs_urls_and_prevents_rerun_leakage(self):
        """New Research clears all results/inputs/dynamic URL slots and prevents stale data after reruns."""
        with self._mock_dns(), patch("analyzer.ResearchSession") as mock_session_cls:
            at = AppTest.from_file("app.py", default_timeout=60).run()
            self.assertEqual(len(at.exception), 0)

            # Configure unrelated app setting in sidebar
            self._find_text_input(at, "gemini_api_key_input").input("sk-preserve-new-research").run()
            at.session_state["unrelated_app_pref"] = "preserve_me"

            urls = [
                "https://alpha.example.org/specs",
                "https://beta.example.net/review",
                "https://gamma.example.com/benchmark",
            ]
            self._run_mocked_session(
                at,
                query="Compare three cloud runtimes",
                preference="latency, memory",
                urls=urls,
                tag="RUN1",
                mock_cls=mock_session_cls,
            )

            self.assertEqual(len(at.exception), 0)
            self.assertIsNotNone(at.session_state["research_results"])
            rendered_md = "\n".join(m.value for m in at.markdown)
            self.assertIn("Executive Summary for RUN1", rendered_md)
            self.assertIn("TopChoice-RUN1", rendered_md)
            self.assertEqual(len(at.dataframe), 1)

            # Activate New Research from Results Dashboard header
            self._find_button(at, "results_new_research_btn").click().run()
            self.assertEqual(len(at.exception), 0)

            # All research inputs, results, flags, errors, and progress indicators must be cleared
            self.assertIsNone(at.session_state["research_results"])
            self.assertFalse(at.session_state["is_researching"])
            self.assertEqual(at.session_state["current_stage"], 1)
            self.assertEqual(at.session_state["stage_message"], "Ready")
            self.assertEqual(at.session_state["research_error"], "")
            self.assertEqual(at.session_state["validation_errors"], [])
            self.assertEqual(at.session_state["active_tab"], "Research")
            self.assertEqual(at.session_state["query_input"], "")
            self.assertEqual(at.session_state["preference_input"], "")
            self.assertEqual(at.session_state["urls_input"], ["", ""])
            self.assertEqual(at.session_state["url_field_0"], "")
            self.assertEqual(at.session_state["url_field_1"], "")
            self.assertNotIn("url_field_2", at.session_state)

            # Previous report content & matrix must no longer be visible
            after_md = "\n".join(m.value for m in at.markdown)
            self.assertNotIn("Executive Summary for RUN1", after_md)
            self.assertNotIn("TopChoice-RUN1", after_md)
            self.assertEqual(len(at.dataframe), 0)

            # Adding a 3rd URL slot afterwards must be blank (old 3rd URL must not resurrect)
            self._find_button(at, "add_url_btn").click().run()
            self.assertEqual(at.session_state["url_field_2"], "")

            # Navigating tabs (forcing multiple Streamlit reruns) must NEVER resurrect old results
            self._find_button(at, "nav_about_btn").click().run()
            self._find_button(at, "nav_research_btn").click().run()
            self.assertIsNone(at.session_state["research_results"])
            rerun_md = "\n".join(m.value for m in at.markdown)
            self.assertNotIn("Executive Summary for RUN1", rerun_md)

            # Unrelated configuration persists cleanly
            self.assertEqual(at.session_state["gemini_api_key_input"], "sk-preserve-new-research")
            self.assertEqual(os.environ.get("GEMINI_API_KEY"), "sk-preserve-new-research")
            self.assertEqual(at.session_state["unrelated_app_pref"], "preserve_me")

    def test_02_new_research_from_about_tab_clears_validation_errors_and_returns_to_workspace(self):
        """New Research works from the About tab and clears validation errors cleanly."""
        with self._mock_dns():
            at = AppTest.from_file("app.py", default_timeout=60).run()

            # Trigger validation error
            self._find_text_input(at, "query_input").input("hi").run()
            self._find_button(at, "start_research_btn").click().run()
            self.assertTrue(len(at.session_state["validation_errors"]) >= 1)
            self.assertTrue(len(at.error) >= 1)

            # Navigate to About, then click top New Research
            self._find_button(at, "nav_about_btn").click().run()
            self.assertEqual(at.session_state["active_tab"], "About")

            self._find_button(at, "top_new_research_btn").click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertEqual(at.session_state["active_tab"], "Research")
            self.assertEqual(at.session_state["query_input"], "")
            self.assertEqual(at.session_state["validation_errors"], [])
            self.assertEqual(len(at.error), 0)

    def test_03_reset_confirmation_cancel_and_confirm_preserves_unrelated_config(self):
        """Reset asks confirmation before clearing active results, supports Cancel, and preserves app settings."""
        with self._mock_dns(), patch("analyzer.ResearchSession") as mock_session_cls:
            at = AppTest.from_file("app.py", default_timeout=60).run()

            self._find_text_input(at, "gemini_api_key_input").input("sk-custom-config-777").run()
            at.session_state["custom_ui_setting"] = "compact_cards"

            urls = ["https://one.example.org/doc", "https://two.example.net/doc"]
            self._run_mocked_session(
                at,
                query="Compare two analytics engines",
                preference="cost, throughput",
                urls=urls,
                tag="RESETTEST",
                mock_cls=mock_session_cls,
            )
            self.assertIsNotNone(at.session_state["research_results"])

            # First Reset click triggers confirmation prompt without losing results yet
            self._find_button(at, "top_reset_btn").click().run()
            self.assertTrue(at.session_state["confirm_reset"])
            self.assertIsNotNone(at.session_state["research_results"])
            self.assertTrue(any(w for w in at.warning if "Reset the research workspace" in w.value))

            # Cancel aborts reset cleanly and preserves active report
            self._find_button(at, "cancel_reset_btn").click().run()
            self.assertFalse(at.session_state["confirm_reset"])
            self.assertIsNotNone(at.session_state["research_results"])
            self.assertEqual(at.session_state["query_input"], "Compare two analytics engines")

            # Confirm Reset wipes all research data/inputs and preserves settings
            self._find_button(at, "top_reset_btn").click().run()
            self._find_button(at, "confirm_reset_btn").click().run()

            self.assertEqual(len(at.exception), 0)
            self.assertFalse(at.session_state["confirm_reset"])
            self.assertIsNone(at.session_state["research_results"])
            self.assertFalse(at.session_state["is_researching"])
            self.assertEqual(at.session_state["current_stage"], 1)
            self.assertEqual(at.session_state["stage_message"], "Ready")
            self.assertEqual(at.session_state["query_input"], "")
            self.assertEqual(at.session_state["preference_input"], "")
            self.assertEqual(at.session_state["urls_input"], ["", ""])
            self.assertEqual(at.session_state["gemini_api_key_input"], "sk-custom-config-777")
            self.assertEqual(os.environ.get("GEMINI_API_KEY"), "sk-custom-config-777")
            self.assertEqual(at.session_state["custom_ui_setting"], "compact_cards")

    def test_04_repeated_research_sessions_isolated_without_retriggering_previous(self):
        """Repeated research sessions execute independently without re-running or mixing prior sessions."""
        with self._mock_dns(), patch("analyzer.ResearchSession") as mock_session_cls:
            at = AppTest.from_file("app.py", default_timeout=60).run()

            # Session 1
            urls_1 = ["https://first-a.example.org/p1", "https://first-b.example.net/p2"]
            self._run_mocked_session(
                at,
                query="First study query",
                preference="focus one",
                urls=urls_1,
                tag="FIRST",
                mock_cls=mock_session_cls,
            )
            self.assertEqual(mock_session_cls.call_count, 1)
            self.assertIn("Executive Summary for FIRST", "\n".join(m.value for m in at.markdown))

            # Start New Research -> must NOT re-trigger Session 1
            self._find_button(at, "top_new_research_btn").click().run()
            self.assertEqual(mock_session_cls.call_count, 1)

            # Session 2
            urls_2 = ["https://second-a.example.org/q1", "https://second-b.example.net/q2"]
            self._run_mocked_session(
                at,
                query="Second study query",
                preference="focus two",
                urls=urls_2,
                tag="SECOND",
                mock_cls=mock_session_cls,
            )
            self.assertEqual(mock_session_cls.call_count, 2)
            second_call_kwargs = mock_session_cls.call_args.kwargs
            self.assertEqual(second_call_kwargs["query"], "Second study query")
            self.assertEqual(second_call_kwargs["urls"], urls_2)

            rendered_md = "\n".join(m.value for m in at.markdown)
            self.assertIn("Executive Summary for SECOND", rendered_md)
            self.assertNotIn("Executive Summary for FIRST", rendered_md)
            self.assertNotIn("First study query", rendered_md)

    def test_05_reset_during_and_after_failed_research_session(self):
        """Reset recovers cleanly after error-dict failure, exception failure, and stuck loading state."""
        with self._mock_dns(), patch("analyzer.ResearchSession") as mock_session_cls:
            at = AppTest.from_file("app.py", default_timeout=60).run()
            self._find_text_input(at, "gemini_api_key_input").input("sk-keep-on-failure").run()

            # A) ResearchSession returns an error payload
            mock_err_instance = MagicMock()
            mock_err_instance.execute.return_value = {
                "error": True,
                "message": "Network extraction failed",
                "errors": ["Site 1 timed out", "Site 2 blocked"],
            }
            mock_session_cls.return_value = mock_err_instance

            self._find_text_input(at, "query_input").input("Failed research attempt").run()
            self._find_text_input(at, "url_field_0").input("https://fail-one.example.org").run()
            self._find_text_input(at, "url_field_1").input("https://fail-two.example.net").run()
            self._find_button(at, "start_research_btn").click().run()

            self.assertEqual(len(at.exception), 0)
            self.assertFalse(at.session_state["is_researching"])
            self.assertIsNone(at.session_state["research_results"])
            self.assertIn("Site 1 timed out", at.session_state["research_error"])
            self.assertTrue(any("Site 1 timed out" in e.value for e in at.error))

            # Reset Form immediately clears error state and restores blank defaults
            self._find_button(at, "form_reset_btn").click().run()
            self.assertEqual(at.session_state["research_error"], "")
            self.assertEqual(at.session_state["query_input"], "")
            self.assertEqual(at.session_state["urls_input"], ["", ""])
            self.assertEqual(at.session_state["current_stage"], 1)
            self.assertEqual(at.session_state["stage_message"], "Ready")
            self.assertEqual(len(at.error), 0)
            self.assertEqual(at.session_state["gemini_api_key_input"], "sk-keep-on-failure")

            # B) ResearchSession raises an unexpected RuntimeError
            mock_exc_instance = MagicMock()
            mock_exc_instance.execute.side_effect = RuntimeError("Unexpected Playwright crash")
            mock_session_cls.return_value = mock_exc_instance

            self._find_text_input(at, "query_input").input("Crashing run query").run()
            self._find_text_input(at, "url_field_0").input("https://crash-one.example.org").run()
            self._find_text_input(at, "url_field_1").input("https://crash-two.example.net").run()
            self._find_button(at, "start_research_btn").click().run()

            self.assertFalse(at.session_state["is_researching"])
            self.assertIn("Unexpected Playwright crash", at.session_state["research_error"])
            self._find_button(at, "top_reset_btn").click().run()
            self.assertEqual(at.session_state["research_error"], "")
            self.assertEqual(at.session_state["query_input"], "")

            # C) Simulate resetting during an interrupted/stuck in-progress run (is_researching=True)
            calls_before = mock_session_cls.call_count
            at.session_state["is_researching"] = True
            at.session_state["current_stage"] = 4
            at.session_state["stage_message"] = "Analyzing Evidence"
            at.session_state["active_query"] = "Stuck run query"
            at.session_state["active_urls"] = ["https://stuck-a.example.org", "https://stuck-b.example.net"]

            self._find_button(at, "top_reset_btn").click().run()
            self.assertEqual(mock_session_cls.call_count, calls_before)
            self.assertFalse(at.session_state["is_researching"])
            self.assertEqual(at.session_state["current_stage"], 1)
            self.assertEqual(at.session_state["stage_message"], "Ready")
            self.assertEqual(at.session_state["active_query"], "")
            self.assertEqual(at.session_state["active_urls"], [])
            self.assertEqual(at.session_state["gemini_api_key_input"], "sk-keep-on-failure")

    def test_06_draft_form_reset_restores_defaults_immediately(self):
        """Resetting draft inputs restores default values in one click without destroying app settings."""
        with self._mock_dns():
            at = AppTest.from_file("app.py", default_timeout=60).run()

            self._find_text_input(at, "gemini_api_key_input").input("sk-draft-keep").run()
            self._find_button(at, "add_url_btn").click().run()
            self._find_text_input(at, "query_input").input("Unsaved draft question").run()
            self._find_text_input(at, "preference_input").input("Draft priority").run()
            self._find_text_input(at, "url_field_0").input("https://draft1.example.org").run()
            self._find_text_input(at, "url_field_2").input("https://draft3.example.org").run()

            # Draft form reset works directly without active-results confirmation banner
            self._find_button(at, "form_reset_btn").click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertFalse(at.session_state["confirm_reset"])
            self.assertEqual(at.session_state["query_input"], "")
            self.assertEqual(at.session_state["preference_input"], "")
            self.assertEqual(at.session_state["urls_input"], ["", ""])
            self.assertEqual(at.session_state["url_field_0"], "")
            self.assertEqual(at.session_state["url_field_1"], "")
            self.assertNotIn("url_field_2", at.session_state)
            self.assertEqual(at.session_state["gemini_api_key_input"], "sk-draft-keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
