"""
WebScout - Research Workflow Orchestrator & Analyzer
Coordinates browser automation, content extraction, and AI synthesis.
Manages research progress states and consolidates structured intelligence reports.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from scraper import scrape_multiple_urls, ScrapedSource
from ai_engine import analyze_with_gemini
from utils import validate_research_inputs, generate_markdown_report

logger = logging.getLogger("WebScoutAnalyzer")
logger.setLevel(logging.INFO)

# Structured milestone stages
STAGES = [
    {"id": 1, "code": "UNDERSTANDING", "label": "Understanding Query", "desc": "Analyzing research objective and comparison parameters"},
    {"id": 2, "code": "NAVIGATING", "label": "Navigating Websites", "desc": "Launching headless browser and accessing target URLs"},
    {"id": 3, "code": "EXTRACTING", "label": "Extracting Information", "desc": "Parsing DOM, stripping noise, and isolating semantic evidence"},
    {"id": 4, "code": "ANALYZING", "label": "Analyzing Evidence", "desc": "Synthesizing source data and verifying claims with Gemini AI"},
    {"id": 5, "code": "COMPARING", "label": "Comparing Findings", "desc": "Building cross-source comparison matrix and detecting discrepancies"},
    {"id": 6, "code": "PREPARING", "label": "Preparing Intelligence Report", "desc": "Finalizing executive summary and recommendations"}
]


class ResearchSession:
    """Manages the full lifecycle of an autonomous multi-website research run."""

    def __init__(self, query: str, urls: List[str], preference: str = "", api_key: Optional[str] = None):
        self.query = query.strip()
        self.urls = [u.strip() for u in urls if u and u.strip()]
        self.preference = preference.strip()
        self.api_key = api_key
        self.current_stage: int = 1
        self.status_message: str = "Ready"
        self.scraped_sources: List[Dict[str, Any]] = []
        self.report: Optional[Dict[str, Any]] = None
        self.markdown_report: str = ""
        self.start_time: float = 0.0
        self.elapsed_time: float = 0.0
        self.errors: List[str] = []

    def execute(self, progress_callback: Optional[Callable[[int, str, Optional[Dict[str, Any]]], None]] = None) -> Dict[str, Any]:
        """
        Executes the 6-stage autonomous research pipeline.
        Invokes progress_callback(stage_id, status_message, extra_data) at each phase.
        """
        self.start_time = time.time()

        def update_progress(stage_num: int, message: str, extra: Optional[Dict[str, Any]] = None):
            self.current_stage = stage_num
            self.status_message = message
            if progress_callback:
                progress_callback(stage_num, message, extra)

        # STAGE 1: QUERY UNDERSTANDING & VALIDATION
        update_progress(1, "Validating research criteria and target URLs...")
        is_valid, validation_errors = validate_research_inputs(self.query, self.urls)
        if not is_valid:
            self.errors.extend(validation_errors)
            update_progress(1, f"Validation failed: {', '.join(validation_errors)}")
            return {"error": True, "message": "Validation failed", "errors": validation_errors}

        time.sleep(0.5)  # Brief visual cadence

        # STAGE 2: NAVIGATING WEBSITES & STAGE 3: EXTRACTING INFORMATION
        update_progress(2, f"Launching headless browser to navigate {len(self.urls)} websites...")

        def site_nav_callback(idx: int, total: int, url: str, status: str):
            if status == "navigating":
                update_progress(2, f"Navigating to [{idx}/{total}]: {url}...")
            else:
                update_progress(3, f"Extracted DOM content from [{idx}/{total}]: status {status}")

        raw_scraped: List[ScrapedSource] = scrape_multiple_urls(
            self.urls,
            progress_callback=site_nav_callback,
            timeout_ms=25000
        )

        self.scraped_sources = [s.to_dict() for s in raw_scraped]

        # Check if at least one source was reached
        accessible_count = sum(1 for s in self.scraped_sources if s["status"] in ("SUCCESS", "PARTIAL"))
        if accessible_count == 0:
            update_progress(3, "Warning: None of the submitted URLs could be retrieved.")
        else:
            update_progress(3, f"Successfully collected clean content from {accessible_count}/{len(self.urls)} websites.")

        time.sleep(0.5)

        # STAGE 4: ANALYZING EVIDENCE
        update_progress(4, "Analyzing extracted evidence with Google Gemini AI...")

        ai_result = analyze_with_gemini(
            query=self.query,
            sources=self.scraped_sources,
            preference=self.preference,
            api_key=self.api_key
        )

        time.sleep(0.5)

        # STAGE 5: COMPARING FINDINGS & DISCREPANCIES
        update_progress(5, "Structuring cross-source matrix and identifying discrepancies...")
        time.sleep(0.5)

        # STAGE 6: PREPARING INTELLIGENCE REPORT
        update_progress(6, "Assembling executive summary, evidence citations, and recommendations...")

        # Consolidate report payload
        final_report = {
            "query": self.query,
            "preference": self.preference,
            "summary": ai_result.get("research_summary", "Synthesis complete."),
            "recommendation": ai_result.get("recommendation", {}).get("verdict", "No recommendation."),
            "recommendation_detail": ai_result.get("recommendation", {}),
            "sources": self.scraped_sources,
            "source_findings": ai_result.get("source_findings", []),
            "comparison": ai_result.get("comparison_matrix", []),
            "discrepancies": ai_result.get("discrepancies", []),
            "pros_and_cons": ai_result.get("pros_and_cons", []),
            "limitations": ai_result.get("limitations", []),
            "is_fallback": ai_result.get("is_fallback", False),
            "model_used": ai_result.get("model_used", "Gemini 2.5 Flash / Built-in Heuristics"),
            "elapsed_seconds": round(time.time() - self.start_time, 2)
        }

        # Generate downloadable markdown
        self.markdown_report = generate_markdown_report(final_report)
        final_report["markdown_content"] = self.markdown_report
        self.report = final_report
        self.elapsed_time = final_report["elapsed_seconds"]

        update_progress(6, f"Research report ready! Completed in {self.elapsed_time}s.", {"report": final_report})
        return final_report
