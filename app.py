"""
WebScout - AI-Powered Multi-Website Research and Intelligence Agent
Frontend Application Built with Streamlit, Playwright, and Google Gemini SDK.
"""

import os
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local environment
load_dotenv()

from utils import validate_research_inputs, DEMO_SCENARIOS
from analyzer import ResearchSession, STAGES

# ---------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="WebScout — Autonomous Multi-Website Research Agent",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System CSS
CUSTOM_CSS = """
<style>
/* Font and Base Theme */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #182230;
}

/* Background */
.stApp {
    background-color: #F8FAFC;
}

/* Header & Typography */
h1, h2, h3, h4 {
    color: #0F172A;
    font-weight: 700;
    letter-spacing: -0.02em;
}

/* Top Branding Bar */
.brand-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0rem 1.5rem 0rem;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 1.5rem;
}
.brand-logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.logo-icon {
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    color: white;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}
.brand-name {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #0F172A 0%, #1E40AF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
}
.brand-tag {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    background: #EFF6FF;
    color: #2563EB;
    border-radius: 9999px;
    border: 1px solid #DBEAFE;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Hero Section */
.hero-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #F1F5F9 100%);
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 2.25rem 2.5rem;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
    margin-bottom: 2rem;
    text-align: left;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.15;
    margin-bottom: 0.75rem;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #475569;
    max-width: 780px;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

/* Input Form Styling */
.input-panel {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04);
    margin-bottom: 2rem;
}

/* Milestone Stepper */
.stepper-container {
    display: flex;
    justify-content: space-between;
    margin: 1.5rem 0;
    padding: 1rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    flex: 1;
    position: relative;
}
.step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    margin-bottom: 0.4rem;
}
.step-number.active {
    background: #2563EB;
    color: #FFFFFF;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2);
}
.step-number.completed {
    background: #10B981;
    color: #FFFFFF;
}
.step-number.upcoming {
    background: #F1F5F9;
    color: #94A3B8;
}
.step-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
}

/* Result Cards */
.result-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    margin-bottom: 1.5rem;
}
.summary-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    color: #F8FAFC;
    border-radius: 14px;
    padding: 1.75rem;
    margin-bottom: 1.75rem;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
}
.summary-card h3 {
    color: #38BDF8;
    margin-top: 0;
}
.recommendation-card {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.75rem;
}
.discrepancy-card {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

/* Status Badges */
.badge-success {
    background-color: #DCFCE7;
    color: #15803D;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-warning {
    background-color: #FEF3C7;
    color: #B45309;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-error {
    background-color: #FEE2E2;
    color: #B91C1C;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Metric Display */
.metric-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
}
.metric-val {
    font-size: 1.8rem;
    font-weight: 800;
    color: #2563EB;
}
.metric-lbl {
    font-size: 0.8rem;
    color: #64748B;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "research_results" not in st.session_state:
    st.session_state.research_results = None
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False
if "current_stage" not in st.session_state:
    st.session_state.current_stage = 1
if "stage_message" not in st.session_state:
    st.session_state.stage_message = "Ready"
if "query_input" not in st.session_state:
    st.session_state.query_input = ""
if "urls_input" not in st.session_state:
    st.session_state.urls_input = ["", ""]
if "preference_input" not in st.session_state:
    st.session_state.preference_input = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Research"


# ---------------------------------------------------------
# SIDEBAR CONFIGURATION
# ---------------------------------------------------------
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=72)
    st.markdown("### ⚙️ Engine Settings")

    configured_key = os.getenv("GEMINI_API_KEY", "")
    is_key_set = bool(configured_key and configured_key != "your_gemini_api_key_here")

    # API Key Input
    user_api_key = st.text_input(
        "Google Gemini API Key",
        value=configured_key if is_key_set else "",
        type="password",
        help="Get your key at https://aistudio.google.com/. Required for AI synthesis; fallback heuristics run if absent."
    )

    if user_api_key:
        os.environ["GEMINI_API_KEY"] = user_api_key
        is_key_set = True

    # Status Pill
    if is_key_set:
        st.markdown('<span class="badge-success">● Gemini API Configured</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-warning">● Heuristic Fallback Mode</span>', unsafe_allow_html=True)
        st.caption("Provide a Gemini API key for deep cross-source semantic reasoning and discrepancy detection.")

    st.markdown("---")
    st.markdown("### 🌐 Browser Automation")
    st.caption("**Engine**: Playwright Headless Chromium")
    st.caption("**Extraction**: BeautifulSoup4 DOM Parser")
    st.caption("**Security**: Anti-SSRF & Loopback Filter Active")

    st.markdown("---")
    st.markdown("### 💡 Quick Demonstration")
    st.caption("Select a pre-configured research scenario to populate the input panel:")

    for idx, scenario in enumerate(DEMO_SCENARIOS):
        if st.button(scenario["label"], key=f"demo_btn_{idx}", use_container_width=True):
            st.session_state.query_input = scenario["query"]
            st.session_state.urls_input = list(scenario["urls"])
            st.session_state.preference_input = scenario["preference"]
            st.session_state.research_results = None
            st.rerun()

    st.markdown("---")
    st.caption("WebScout v1.0 • Hackathon Edition")


# ---------------------------------------------------------
# TOP NAVIGATION & BRANDING BAR
# ---------------------------------------------------------
st.markdown(
    """
    <div class="brand-container">
        <div class="brand-logo">
            <div class="logo-icon">🌐</div>
            <div>
                <span class="brand-name">WebScout</span>
                <span class="brand-tag">Autonomous Agent</span>
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #64748B; font-weight: 500;">
            "Research smarter. Compare faster. Decide confidently."
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# MAIN VIEWS: RESEARCH WORKSPACE & ABOUT
# ---------------------------------------------------------
nav_col1, nav_col2, _ = st.columns([1, 1, 4])
with nav_col1:
    if st.button("🔍 Research Studio", use_container_width=True, type="primary" if st.session_state.active_tab == "Research" else "secondary"):
        st.session_state.active_tab = "Research"
        st.rerun()
with nav_col2:
    if st.button("ℹ️ Architecture & About", use_container_width=True, type="primary" if st.session_state.active_tab == "About" else "secondary"):
        st.session_state.active_tab = "About"
        st.rerun()


# =========================================================
# TAB 1: RESEARCH STUDIO
# =========================================================
if st.session_state.active_tab == "Research":

    # HERO HEADER
    if not st.session_state.research_results and not st.session_state.is_researching:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-title">Your research. On autopilot.</div>
                <div class="hero-subtitle">
                    WebScout autonomously navigates target websites with headless browser automation, 
                    extracts clean verifiable evidence, reconciles discrepancies, and synthesizes source-backed 
                    comparisons and actionable recommendations.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # RESEARCH INPUT PANEL (Shown when no active results or when user requests new run)
    if not st.session_state.is_researching:
        with st.container():
            st.markdown("### 🎯 Define Your Research Objective")
            
            # Query input
            query_val = st.text_input(
                "Research Question / Goal *",
                value=st.session_state.query_input,
                placeholder="e.g. Compare budget laptops suitable for computer science students.",
                help="Formulate a clear comparative question."
            )

            # Preference input
            pref_val = st.text_input(
                "Evaluation Focus / Priorities (Optional)",
                value=st.session_state.preference_input,
                placeholder="e.g. Price vs. specs, battery life, keyboard quality, long-term durability"
            )

            st.markdown("#### 🔗 Target Source URLs (Minimum 2 distinct websites)")
            
            current_urls = list(st.session_state.urls_input)
            # Ensure at least 2 slots
            while len(current_urls) < 2:
                current_urls.append("")

            url_inputs = []
            for i in range(len(current_urls)):
                url_col, _ = st.columns([5, 1])
                with url_col:
                    u_val = st.text_input(
                        f"Website URL #{i+1}",
                        value=current_urls[i],
                        key=f"url_field_{i}",
                        placeholder="https://example.com/specifications"
                    )
                    url_inputs.append(u_val)

            btn_row1, btn_row2, _ = st.columns([1.5, 1.5, 4])
            with btn_row1:
                if len(current_urls) < 5 and st.button("➕ Add Another URL"):
                    current_urls.append("")
                    st.session_state.urls_input = current_urls
                    st.rerun()
            with btn_row2:
                if len(current_urls) > 2 and st.button("➖ Remove URL"):
                    current_urls.pop()
                    st.session_state.urls_input = current_urls
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            
            col_cta, col_clear, _ = st.columns([2, 1, 3])
            start_clicked = False
            with col_cta:
                if st.button("START RESEARCH →", type="primary", use_container_width=True):
                    start_clicked = True
            with col_clear:
                if st.button("Clear Form", use_container_width=True):
                    st.session_state.query_input = ""
                    st.session_state.urls_input = ["", ""]
                    st.session_state.preference_input = ""
                    st.session_state.research_results = None
                    st.rerun()

            if start_clicked:
                clean_urls = [u.strip() for u in url_inputs if u and u.strip()]
                is_valid, validation_errors = validate_research_inputs(query_val, clean_urls)

                if not is_valid:
                    for err in validation_errors:
                        st.error(f"⚠️ {err}")
                else:
                    st.session_state.query_input = query_val
                    st.session_state.urls_input = clean_urls
                    st.session_state.preference_input = pref_val
                    st.session_state.is_researching = True
                    st.session_state.research_results = None
                    st.rerun()

    # ACTIVE RESEARCH EXECUTION WORKSPACE
    if st.session_state.is_researching:
        st.markdown(f"### ⚡ Research in Progress: *{st.session_state.query_input}*")
        
        # Milestone Stepper Component
        step_cols = st.columns(6)
        stage_placeholders = []
        for i, s in enumerate(STAGES):
            with step_cols[i]:
                p = st.empty()
                stage_placeholders.append(p)

        def render_stepper(current_stage_id: int):
            for i, s in enumerate(STAGES):
                stage_num = s["id"]
                if stage_num < current_stage_id:
                    badge_class = "completed"
                    num_display = "✓"
                elif stage_num == current_stage_id:
                    badge_class = "active"
                    num_display = f"0{stage_num}"
                else:
                    badge_class = "upcoming"
                    num_display = f"0{stage_num}"

                html = f"""
                <div class="step-item">
                    <div class="step-number {badge_class}">{num_display}</div>
                    <div class="step-label">{s['label']}</div>
                </div>
                """
                stage_placeholders[i].markdown(html, unsafe_allow_html=True)

        render_stepper(1)
        
        status_box = st.empty()
        log_box = st.empty()

        session = ResearchSession(
            query=st.session_state.query_input,
            urls=st.session_state.urls_input,
            preference=st.session_state.preference_input,
            api_key=user_api_key or os.getenv("GEMINI_API_KEY")
        )

        def on_progress(stage_num: int, message: str, extra=None):
            render_stepper(stage_num)
            status_box.info(f"**Stage {stage_num}/6**: {message}")

        # Run pipeline
        report = session.execute(progress_callback=on_progress)

        if report and not report.get("error"):
            st.session_state.research_results = report
            st.session_state.is_researching = False
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.is_researching = False
            st.error("Research encountered an issue. See details above.")


    # =========================================================
    # RESULTS DASHBOARD
    # =========================================================
    if st.session_state.research_results and not st.session_state.is_researching:
        res = st.session_state.research_results
        
        # Top Action Bar
        r_col1, r_col2 = st.columns([4, 1.5])
        with r_col1:
            st.markdown(f"## 📊 Research Intelligence: *{res.get('query')}*")
        with r_col2:
            c1, c2 = st.columns(2)
            with c1:
                # Markdown Download
                st.download_button(
                    label="📥 Export Report",
                    data=res.get("markdown_content", ""),
                    file_name="webscout_intelligence_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with c2:
                if st.button("🔄 New Research", use_container_width=True):
                    st.session_state.research_results = None
                    st.session_state.query_input = ""
                    st.session_state.urls_input = ["", ""]
                    st.session_state.preference_input = ""
                    st.rerun()

        # METRICS ROW
        m1, m2, m3, m4 = st.columns(4)
        sources_list = res.get("sources", [])
        success_sources = [s for s in sources_list if s.get("status") in ("SUCCESS", "PARTIAL")]
        with m1:
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{len(success_sources)}/{len(sources_list)}</div><div class="metric-lbl">Sources Verified</div></div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{res.get("elapsed_seconds", 0)}s</div><div class="metric-lbl">Analysis Time</div></div>',
                unsafe_allow_html=True
            )
        with m3:
            disc_count = len(res.get("discrepancies", []))
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{disc_count}</div><div class="metric-lbl">Discrepancies Detected</div></div>',
                unsafe_allow_html=True
            )
        with m4:
            engine_name = "Gemini Flash" if not res.get("is_fallback") else "Heuristic"
            st.markdown(
                f'<div class="metric-box"><div class="metric-val" style="font-size: 1.3rem; padding-top: 0.35rem;">{engine_name}</div><div class="metric-lbl">Engine Mode</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # EXECUTIVE SUMMARY CARD
        st.markdown(
            f"""
            <div class="summary-card">
                <h3>Executive Summary</h3>
                <p style="font-size: 1.05rem; line-height: 1.7; margin: 0; color: #E2E8F0;">
                    {res.get('summary', 'Summary not available.')}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # AI RECOMMENDATION & ACTIONABLE VERDICT
        rec = res.get("recommendation_detail", {})
        verdict = rec.get("verdict", res.get("recommendation", "No verdict generated."))
        reasoning = rec.get("reasoning", "")
        top_pick = rec.get("top_choice_or_conclusion", "")
        supporting = rec.get("supporting_sources", [])

        st.markdown(
            f"""
            <div class="recommendation-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h3 style="color: #166534; margin: 0;">🎯 Actionable Recommendation</h3>
                    {f'<span class="badge-success" style="font-size: 0.85rem;">Top Choice: {top_pick}</span>' if top_pick else ''}
                </div>
                <p style="font-size: 1.1rem; font-weight: 600; color: #15803D; margin-top: 0.75rem; margin-bottom: 0.5rem;">
                    {verdict}
                </p>
                <p style="color: #374151; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0.75rem;">
                    {reasoning}
                </p>
                {f'<div style="font-size: 0.8rem; color: #64748B;"><b>Supporting Sources:</b> {", ".join(supporting)}</div>' if supporting else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

        # SECTION C: INDIVIDUAL SOURCE FINDINGS & VERIFIABLE EVIDENCE
        st.markdown("### 🔍 Evaluated Sources & Grounded Evidence")
        st.caption("Every finding is directly tied to an extracted webpage. Click source links to audit original content.")

        source_cols = st.columns(len(sources_list) if len(sources_list) <= 3 else 3)
        findings_map = {sf["source_url"]: sf for sf in res.get("source_findings", [])}

        for idx, src in enumerate(sources_list):
            col_target = source_cols[idx % len(source_cols)]
            with col_target:
                status = src.get("status", "UNKNOWN")
                badge_class = "badge-success" if status == "SUCCESS" else ("badge-warning" if status == "PARTIAL" else "badge-error")
                url = src.get("url", "#")
                title = src.get("title") or "Website Document"
                char_count = src.get("character_count", 0)
                fetch_time = src.get("fetch_duration_seconds", 0)

                finding_data = findings_map.get(url, {})
                key_pts = finding_data.get("key_findings", src.get("key_snippets", [])[:3])
                evidence_quotes = finding_data.get("evidence_snippets", [])

                with st.container():
                    st.markdown(
                        f"""
                        <div class="result-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <span class="{badge_class}">Status: {status}</span>
                                <span style="font-size: 0.75rem; color: #94A3B8;">{fetch_time}s • {char_count} chars</span>
                            </div>
                            <h4 style="margin: 0.25rem 0 0.5rem 0; font-size: 1.05rem;">{title}</h4>
                            <a href="{url}" target="_blank" style="font-size: 0.8rem; color: #2563EB; text-decoration: none; word-break: break-all;">
                                🔗 {url}
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Points
                    if key_pts:
                        st.markdown("**Key Findings:**")
                        for pt in key_pts:
                            st.markdown(f"• {pt}")

                    # Raw Evidence Accordion
                    with st.expander("📄 View Extracted Evidence Snippets"):
                        if evidence_quotes:
                            for q in evidence_quotes:
                                st.markdown(f"> *\"{q}\"*")
                        elif src.get("key_snippets"):
                            for s in src["key_snippets"][:3]:
                                st.markdown(f"> *\"{s}\"*")
                        else:
                            st.caption("No text excerpts extracted.")

                        if src.get("error_message"):
                            st.warning(f"Note: {src['error_message']}")

        st.markdown("<br>", unsafe_allow_html=True)

        # SECTION D: CROSS-SOURCE COMPARISON MATRIX
        st.markdown("### ⚖️ Cross-Source Comparison Matrix")
        comparison_data = res.get("comparison", [])
        if comparison_data:
            table_rows = []
            for item in comparison_data:
                crit = item.get("criterion", "Feature")
                evals = item.get("source_evaluations", {})
                eval_str = " | ".join([f"{k}: {v}" for k, v in evals.items()])
                note = item.get("synthesis_note", "")
                table_rows.append({
                    "Criterion": crit,
                    "Source Evidence & Evaluations": eval_str,
                    "Comparative Synthesis": note
                })
            df_comp = pd.DataFrame(table_rows)
            st.dataframe(df_comp, use_container_width=True, hide_index=True)
        else:
            st.info("No comparative criteria could be established from the retrieved sources.")

        st.markdown("<br>", unsafe_allow_html=True)

        # SECTION E: DISCREPANCIES & CONFLICTING CLAIMS
        st.markdown("### ⚡ Discrepancy & Contradiction Alerts")
        discrepancies = res.get("discrepancies", [])
        if discrepancies:
            for disc in discrepancies:
                crit = disc.get("criterion", "Discrepancy")
                desc = disc.get("description", "")
                conf_sources = ", ".join(disc.get("conflicting_sources", []))
                res_status = disc.get("resolution_status", "Unresolved")

                st.markdown(
                    f"""
                    <div class="discrepancy-card">
                        <div style="font-weight: 700; color: #92400E; font-size: 0.95rem;">
                            ⚠️ Discrepancy in {crit}
                        </div>
                        <div style="font-size: 0.9rem; color: #451A03; margin: 0.4rem 0;">
                            {desc}
                        </div>
                        <div style="font-size: 0.8rem; color: #78350F;">
                            <b>Conflicting Sources:</b> {conf_sources} | <b>Status:</b> {res_status}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.success("✅ No conflicting claims or contradictions detected between the verified sources.")

        st.markdown("<br>", unsafe_allow_html=True)

        # SECTION F: PROS & CONS PER SOURCE
        pros_cons = res.get("pros_and_cons", [])
        if pros_cons:
            st.markdown("### 🛡️ Strengths & Weaknesses Breakdown")
            pc_cols = st.columns(len(pros_cons) if len(pros_cons) <= 3 else 3)
            for idx, pc in enumerate(pros_cons):
                col = pc_cols[idx % len(pc_cols)]
                with col:
                    st.markdown(f"#### {pc.get('source_name', 'Source')}")
                    for adv in pc.get("advantages", []):
                        st.markdown(f"🟢 **+** {adv}")
                    for dis in pc.get("disadvantages", []):
                        st.markdown(f"🔴 **-** {dis}")

        st.markdown("<br>", unsafe_allow_html=True)

        # SECTION G: RESEARCH LIMITATIONS
        limitations = res.get("limitations", [])
        if limitations:
            st.markdown("### ⚠️ Research Scope & Technical Limitations")
            for lim in limitations:
                st.caption(f"• {lim}")


# =========================================================
# TAB 2: ARCHITECTURE & ABOUT
# =========================================================
elif st.session_state.active_tab == "About":
    st.markdown("## 🏛️ WebScout Product Architecture & Philosophy")
    
    st.markdown(
        """
        ### 1. Vision & Core Philosophy
        WebScout transforms the tedious manual research process of opening dozens of tabs, 
        evaluating specifications, and taking notes into an autonomous, verifiable workflow.
        
        **Three Guiding Principles:**
        1. **Intelligence**: Understands what the user wants to research and dynamically identifies relevant evaluation criteria.
        2. **Transparency & Grounding**: Eliminates AI hallucination by anchoring every single claim to extracted DOM content and raw citations.
        3. **Actionability**: Produces clear comparison matrices, discrepancy alerts, and decisive recommendations rather than vague conversational fluff.
        
        ---
        
        ### 2. Technical Pipeline
        ```
        [User Query + Target URLs]
                    │
                    ▼
        ┌─────────────────────────┐
        │ 1. SSRF & Scheme Filter │ (Validates HTTP/HTTPS, blocks localhost/loopbacks)
        └───────────┬─────────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ 2. Playwright Headless  │ (Chromium renders dynamic SPAs & pages)
        └───────────┬─────────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ 3. BeautifulSoup4 Clean │ (Strips cookie banners, scripts, ads, and noise)
        └───────────┬─────────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ 4. Google Gemini SDK    │ (Schema-constrained prompt with untrusted data bounds)
        └───────────┬─────────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ 5. Discrepancy & Matrix │ (Detects contradictions & synthesizes findings)
        └───────────┬─────────────┘
                    │
                    ▼
        [Interactive Intelligence Dashboard + Markdown Export]
        ```
        
        ---
        
        ### 3. Security & Anti-Prompt-Injection Safeguards
        - **Untrusted Web Content Quarantine**: All scraped text is treated as evidence and enclosed within strict delimiter boundaries. Instructions inside scraped pages are neutralized by strict system prompt guidelines.
        - **SSRF & Network Isolation**: Only public HTTP/HTTPS URLs are allowed. Hostnames resolving to private IP ranges (127.0.0.1, 10.x, 192.168.x, 169.254.x) are rejected prior to navigation.
        - **Per-Site Fault Tolerance**: Playwright operates with configurable timeouts (25s) and per-site try/catch logic. If one website fails or blocks automated browsing, the remaining sources continue uninterrupted.
        
        ---
        
        ### 4. Technology Stack
        - **Frontend**: Streamlit with custom CSS design tokens
        - **Browser Automation**: Playwright (Headless Chromium)
        - **DOM Parsing**: BeautifulSoup4 + lxml
        - **AI Engine**: Google Gemini API via official `google-genai` SDK
        - **Environment**: Python 3.13, python-dotenv, Pydantic v2
        """
    )
