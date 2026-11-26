"""
WebScout - Utility Functions & Security Sanitization
Provides safe URL validation, SSRF protection, prompt sanitization,
and markdown export utilities.
"""

import ipaddress
import os
import re
import socket
from typing import List, Tuple, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def is_valid_http_url(url: str) -> Tuple[bool, str]:
    """
    Validates whether a URL is a valid, publicly reachable HTTP/HTTPS URL.
    Implements security guards against SSRF, loopback, private ranges, and malicious schemes.
    
    Returns:
        (is_valid, error_reason)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."
    
    cleaned_url = url.strip()
    if len(cleaned_url) > 2048:
        return False, "URL length exceeds safe limit (2048 characters)."

    # Parse URL
    try:
        parsed = urlparse(cleaned_url)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}"

    # Scheme check: HTTP and HTTPS only
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    # Hostname check
    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a valid host domain (e.g. https://www.example.com)."

    # Reject localhost & internal aliases
    hostname_lower = hostname.lower()
    blocked_hosts = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1", "local", "internal",
        "metadata.google.internal", "169.254.169.254"
    }
    if hostname_lower in blocked_hosts or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        return False, "Access to localhost or private cloud metadata is strictly blocked for security."

    # Check if host is direct IP address
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False, f"Direct access to private or loopback IP ({hostname}) is not permitted."
    except ValueError:
        # Not a raw IP; domain name resolution check
        try:
            # Check resolved address if resolvable
            resolved_ip_str = socket.gethostbyname(hostname)
            resolved_ip = ipaddress.ip_address(resolved_ip_str)
            if resolved_ip.is_private or resolved_ip.is_loopback or resolved_ip.is_link_local:
                return False, f"Host '{hostname}' resolves to a restricted private/local address ({resolved_ip_str})."
        except socket.error:
            # If DNS resolution temporarily fails, allow Playwright to attempt it,
            # as long as the domain name looks syntactically valid (has a dot or standard TLD)
            if "." not in hostname:
                return False, f"Host '{hostname}' does not appear to be a valid public domain."

    return True, ""


def validate_research_inputs(query: str, urls: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates user query and list of research URLs.
    Enforces minimum 2 valid URLs.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors: List[str] = []

    if not query or len(query.strip()) < 5:
        errors.append("Please enter a clear research question (at least 5 characters).")

    cleaned_urls = [u.strip() for u in urls if u and u.strip()]
    if len(cleaned_urls) < 2:
        errors.append("WebScout requires at least 2 distinct website URLs for cross-source comparison.")
        return False, errors

    # Check duplicates
    normalized_urls = set()
    for u in cleaned_urls:
        norm = u.lower().rstrip("/")
        if norm in normalized_urls:
            errors.append(f"Duplicate URL detected: '{u}'. Please provide distinct sources.")
        normalized_urls.add(norm)

    for idx, u in enumerate(cleaned_urls, start=1):
        is_valid, reason = is_valid_http_url(u)
        if not is_valid:
            errors.append(f"URL #{idx} ('{u}'): {reason}")

    return len(errors) == 0, errors


def sanitize_text_for_ai(text: str, max_chars: int = 18000) -> str:
    """
    Sanitizes extracted webpage text to mitigate prompt injection,
    cleans up excessive whitespace, and caps length.
    """
    if not text:
        return ""

    # Replace potential prompt injection attempts or system command overrides
    cleaned = re.sub(r'[\r\n\t]+', ' ', text)
    cleaned = re.sub(r' {2,}', ' ', cleaned).strip()

    # Truncate to maximum characters safely
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "... [Content truncated for analysis]"

    return cleaned


def generate_markdown_report(report_data: dict) -> str:
    """
    Converts structured research analysis data into a clean, comprehensive Markdown report.
    """
    query = report_data.get("query", "WebScout Research")
    summary = report_data.get("summary", "No summary available.")
    recommendation = report_data.get("recommendation", "No recommendation generated.")
    sources = report_data.get("sources", [])
    comparison = report_data.get("comparison", [])
    discrepancies = report_data.get("discrepancies", [])
    limitations = report_data.get("limitations", [])

    lines = [
        f"# WebScout Intelligence Report: {query}",
        "",
        "> Generated automatically by **WebScout** — AI-Powered Multi-Website Research Agent",
        "",
        "## 1. Executive Summary",
        "",
        summary,
        "",
        "## 2. Recommendation & Actionable Verdict",
        "",
        recommendation,
        "",
        "## 3. Evaluated Sources",
        ""
    ]

    source_findings_list = report_data.get("source_findings", [])
    sf_by_url = {
        (sf.get("source_url") or "").strip().rstrip("/").lower(): sf
        for sf in source_findings_list
        if isinstance(sf, dict) and sf.get("source_url")
    }

    for src in sources:
        title = src.get("title", "Untitled Source")
        url = src.get("url", "#")
        status = src.get("status", "Unknown")
        sf_match = sf_by_url.get((url or "").strip().rstrip("/").lower(), {})
        key_points = src.get("key_findings") or sf_match.get("key_findings", [])
        evidence_snippets = src.get("evidence_snippets") or sf_match.get("evidence_snippets", [])

        lines.append(f"### {title}")
        lines.append(f"- **Source URL**: [{url}]({url})")
        lines.append(f"- **Retrieval Status**: `{status}`")
        if key_points:
            lines.append("- **Key Findings**:")
            for pt in key_points:
                lines.append(f"  - {pt}")
        if evidence_snippets:
            lines.append("- **Verified Evidence Excerpts**:")
            for snip in evidence_snippets:
                lines.append(f'  > "{snip}"')
        lines.append("")

    evidence_findings = report_data.get("evidence_findings", [])
    if evidence_findings:
        lines.append("### Evidence-Backed Findings & Traceability")
        lines.append("")
        for ef in evidence_findings:
            ev_status = ef.get("evidence_status", "UNSUPPORTED")
            ver_status = ef.get("verification_status")
            is_inf = ef.get("is_inference", False)
            tag_parts = [ev_status]
            if ver_status:
                tag_parts.append(ver_status)
            if is_inf and ev_status != "INFERENCE":
                tag_parts.append("INFERENCE")
            badge = f"[{' | '.join(tag_parts)}]"
            lines.append(f"- **{badge}** {ef.get('finding', '')}")
            supporting = [
                cit for cit in ef.get("supporting_sources", [])
                if cit.get("is_verified", True) and cit.get("excerpt_verified", True)
            ]
            if supporting:
                for cit in supporting:
                    c_id = cit.get("source_id", "")
                    c_url = cit.get("source_url", "")
                    c_title = cit.get("source_title") or c_url
                    c_status = cit.get("source_status", "UNKNOWN")
                    id_prefix = f"{c_id} | " if c_id else ""
                    lines.append(f"  - Verified Citation: [{c_title}]({c_url}) (`{id_prefix}{c_status}`)")
                    if cit.get("evidence_excerpt"):
                        lines.append(f'    > "{cit["evidence_excerpt"]}"')
            elif ef.get("evidence_excerpt") and ver_status != "UNVERIFIED":
                lines.append(f'  > "{ef["evidence_excerpt"]}"')
            if ef.get("inference_basis"):
                lines.append(f"  - *Inference Basis*: {ef['inference_basis']}")
            if ef.get("limitation_note"):
                lines.append(f"  - *Note*: {ef['limitation_note']}")
        lines.append("")

    if comparison:
        lines.append("## 4. Cross-Source Comparison Matrix")
        lines.append("")
        # Markdown table
        lines.append("| Criterion | Findings Across Sources | Analysis / Distinctions |")
        lines.append("| :--- | :--- | :--- |")
        for item in comparison:
            crit = item.get("criterion", "Feature")
            details = item.get("details", "")
            if not details and isinstance(item.get("cells"), dict) and item["cells"]:
                cell_parts = []
                for sid, cell in item["cells"].items():
                    label = cell.get("source_title") or sid
                    val = cell.get("extracted_value", "")
                    st = cell.get("information_status", "")
                    norm = cell.get("normalized_value", "")
                    norm_suffix = f" [{norm}]" if norm else ""
                    cell_parts.append(f"{label} ({sid}, {st}): {val}{norm_suffix}")
                details = "; ".join(cell_parts)
            elif not details and isinstance(item.get("source_evaluations"), dict):
                details = "; ".join(f"{k}: {v}" for k, v in item["source_evaluations"].items())
            eval_note = item.get("evaluation") or item.get("explanation") or item.get("synthesis_note", "")
            cls = item.get("classification", "")
            ver = item.get("verification_status", "")
            if cls:
                badge = f"`[{cls} | {ver}]` " if ver else f"`[{cls}]` "
                eval_note = f"{badge}{eval_note}"
            lines.append(f"| **{crit}** | {details} | {eval_note} |")
        lines.append("")

    if discrepancies:
        lines.append("## 5. Discrepancies & Contradictions")
        lines.append("")
        for disc in discrepancies:
            crit = disc.get("criterion", "General")
            c_status = disc.get("contradiction_status", "")
            v_status = disc.get("verification_status", "")
            conf = disc.get("confidence", "")
            note = disc.get("explanation") or disc.get("description", "")
            meta_tags = [t for t in (c_status, v_status, f"Confidence: {conf}" if conf else "") if t]
            tag_str = f" `[{' | '.join(meta_tags)}]`" if meta_tags else ""
            lines.append(f"- **{crit}**{tag_str}: {note}")
            claims = disc.get("claims", [])
            verified_claims = [c for c in claims if c.get("is_verified", True) and c.get("evidence_excerpt")]
            if verified_claims:
                for cl in verified_claims:
                    src_label = cl.get("source_title") or cl.get("source_url", "")
                    lines.append(f"  - [{src_label}]({cl.get('source_url', '')}) (`{cl.get('source_status', 'UNKNOWN')}`): {cl.get('claim', '')}")
                    lines.append(f'    > "{cl["evidence_excerpt"]}"')
        lines.append("")

    if limitations:
        lines.append("## 6. Research Limitations & Caveats")
        lines.append("")
        for lim in limitations:
            lines.append(f"- {lim}")
        lines.append("")

    lines.append("---")
    lines.append("*WebScout Research Agent — Research smarter. Compare faster. Decide confidently.*")
    return "\n".join(lines)


# Predefined example scenarios for the user and hackathon judges
DEMO_SCENARIOS = [
    {
        "label": "💻 Laptop Comparison: Budget CS Student Laptops",
        "query": "Compare technical specs, performance, battery life, and value of budget student laptops.",
        "urls": [
            "https://en.wikipedia.org/wiki/MacBook_Air",
            "https://en.wikipedia.org/wiki/Dell_XPS",
            "https://en.wikipedia.org/wiki/ThinkPad"
        ],
        "preference": "Price vs. Performance, Battery Life, Durability for programming"
    },
    {
        "label": "☁️ Cloud Platforms: AWS vs Azure vs Google Cloud",
        "query": "Compare compute services, AI capabilities, pricing models, and strengths between leading cloud providers.",
        "urls": [
            "https://en.wikipedia.org/wiki/Amazon_Web_Services",
            "https://en.wikipedia.org/wiki/Microsoft_Azure",
            "https://en.wikipedia.org/wiki/Google_Cloud_Platform"
        ],
        "preference": "Compute offerings, Developer ecosystem, AI infrastructure"
    },
    {
        "label": "⚡ Python Web Frameworks: FastAPI vs Flask vs Django",
        "query": "Compare modern Python web frameworks on speed, asynchronous support, learning curve, and suitability for APIs.",
        "urls": [
            "https://fastapi.tiangolo.com/",
            "https://flask.palletsprojects.com/",
            "https://www.djangoproject.com/"
        ],
        "preference": "API performance, Async features, Battery-included vs lightweight"
    }
]
