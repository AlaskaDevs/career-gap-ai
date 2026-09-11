"""CareerGap AI — single-page scrolling layout.

Each step reveals itself once the previous step's output is ready.
No tabs required — the user simply scrolls down.
"""
from __future__ import annotations

import os
from typing import Any

import streamlit as st

import db
import logic
from ui_components import (
    display_analysis_header,
    display_gap_summary,
    display_job_card,
    display_project_card,
    display_roadmap_card,
    display_skill_coverage_chart,
    display_skill_group,
)

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CareerGap AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

_MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB (must match .streamlit/config.toml)


# ── Session state defaults ───────────────────────────────────────────────────
def _init_state() -> None:
    defaults: dict[str, Any] = {
        "resume_text": None,
        "resume_data": None,
        "resume_id": None,
        "last_uploaded": None,
        "jobs": [],
        "selected_job": None,
        "job_id": None,
        "job_data": None,
        "analysis": None,
        "analysis_id": None,
        "roadmap": [],
        "project": None,
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)

    if "db_initialized" not in st.session_state:
        db.init_db()
        st.session_state.db_initialized = True


_init_state()

# ── Sidebar — progress tracker ───────────────────────────────────────────────
with st.sidebar:
    st.title("🎯 CareerGap AI")
    st.caption("Scroll through your analysis below.")
    st.divider()

    def _tick(done: bool) -> str:
        return "✅" if done else "⬜"

    has_resume  = bool(st.session_state.resume_data)
    has_job     = bool(st.session_state.job_data)
    has_gap     = bool(st.session_state.analysis)
    has_roadmap = bool(st.session_state.roadmap)

    st.markdown(f"""
{_tick(has_resume)} **Step 1** — Upload & Analyze Resume  
{_tick(has_job)}    **Step 2** — Select a Job  
{_tick(has_gap)}    **Step 3** — Skill Gap Analysis  
{_tick(has_roadmap)} **Step 4** — Roadmap & Portfolio  
""")
    st.divider()

    if has_gap:
        score = st.session_state.analysis.get("match_score", 0)
        role  = st.session_state.analysis.get("target_role", "—")
        st.metric("Match score", f"{score}%")
        st.caption(f"Role: {role}")

    st.divider()
    st.caption(
        "CareerGap AI compares your skills with real job requirements "
        "and builds a personalized path to close the gap."
    )

# ── Hero header ──────────────────────────────────────────────────────────────
st.title("🎯 CareerGap AI")
st.subheader("Resume → Skill Gap → Learning Roadmap → Career Growth")
st.write(
    "Upload your resume, pick a real job, see exactly where your skills gap is, "
    "and get a personalized 4-week plan to become job-ready. Just scroll down."
)
st.divider()

# ============================================================================
# STEP 1 — RESUME
# ============================================================================
st.header("📄 Step 1 · Upload & Analyze Your Resume")

uploaded_resume = st.file_uploader(
    "Drop your resume here (PDF, DOCX, or TXT · max 25 MB)",
    type=["pdf", "docx", "txt"],
    key="resume_upload",
)

if uploaded_resume is not None:
    # Client-side size guard (server enforces 25 MB via config.toml)
    if uploaded_resume.size > _MAX_UPLOAD_BYTES:
        st.error(
            f"File is {uploaded_resume.size / 1024 / 1024:.1f} MB — "
            "please upload a file smaller than 25 MB."
        )
    else:
        # Extract text once per file — clear ALL downstream state when file changes
        if st.session_state.last_uploaded != uploaded_resume.name:
            try:
                with st.spinner("Extracting text from your resume\u2026"):
                    st.session_state.resume_text  = logic.extract_text(uploaded_resume)
                    st.session_state.last_uploaded = uploaded_resume.name
                    # Clear stale downstream results so old score is never shown for new resume
                    st.session_state.resume_data   = None
                    st.session_state.resume_id     = None
                    st.session_state.analysis      = None
                    st.session_state.analysis_id   = None
                    st.session_state.roadmap       = []
                    st.session_state.project       = None
            except Exception:
                st.error(
                    "Could not read the file. Please check it is a valid PDF, DOCX, or TXT "
                    "and try again."
                )

        if st.session_state.resume_text:
            # Sanitize filename display — use only the basename, cap length
            safe_name = os.path.basename(uploaded_resume.name)[:100]
            st.success(
                f"\u2705 **{safe_name}** extracted "
                f"({uploaded_resume.size / 1024:.0f} KB)"
            )
            with st.expander("Preview extracted text"):
                st.text(st.session_state.resume_text[:2500])

            if st.button("\U0001f50d Analyze Resume with AI", type="primary", key="btn_analyze_resume"):
                with st.spinner("Analyzing your resume with Gemini\u2026"):
                    try:
                        profile = logic.analyze_resume(st.session_state.resume_text)
                        st.session_state.resume_data = profile
                        st.session_state.resume_id = db.save_resume(
                            safe_name,
                            st.session_state.resume_text,
                            profile,
                        )
                        st.rerun()
                    except Exception as exc:
                        # Show the friendly message from logic layer, not raw exception
                        st.error(str(exc) if str(exc) else "Resume analysis failed. Please try again.")
else:
    st.info("Upload a PDF, DOCX, or TXT resume to begin.", icon="\U0001f4c4")

# Show parsed profile when ready
if st.session_state.resume_data:
    profile = st.session_state.resume_data
    with st.container(border=True):
        st.subheader(f"👤 {profile.get('name') or 'Candidate Profile'}")
        col_a, col_b = st.columns(2)
        with col_a:
            if profile.get("target_roles"):
                st.markdown("**Target Roles**")
                st.write(" · ".join(profile["target_roles"]))
            if profile.get("skills"):
                st.markdown("**Skills**")
                st.write(", ".join(profile["skills"]))
        with col_b:
            if profile.get("experience"):
                st.markdown("**Experience**")
                for exp in profile["experience"]:
                    st.write(f"- {exp}")
            if profile.get("education"):
                st.markdown("**Education**")
                for edu in profile["education"]:
                    st.write(f"- {edu}")

st.divider()

# ============================================================================
# STEP 2 — JOB SELECTION
# ============================================================================
st.header("🎯 Step 2 · Select a Target Job")

if not st.session_state.resume_data:
    st.info("Complete Step 1 (analyze your resume) to unlock this step.", icon="🔒")
else:
    input_mode = st.segmented_control(
        "How do you want to find a job?",
        ["🔎 Search Jobs", "📝 Paste Job Description"],
        default="🔎 Search Jobs",
        key="job_input_mode",
    )

    if input_mode == "🔎 Search Jobs":
        with st.form("job_search_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Job title", placeholder="e.g. Python Developer", key="job_title")
                st.selectbox("Experience", ["Any", "0–2 years", "3–5 years", "5+ years"], key="job_experience")
            with c2:
                st.text_input("Location", placeholder="e.g. Hyderabad", key="job_location")
                st.selectbox("Job type", ["Any", "Full-time", "Internship", "Contract"], key="job_type")
            searched = st.form_submit_button("🔎 Search", type="primary")

        if searched:
            with st.spinner("Generating relevant job listings with AI…"):
                st.session_state.jobs = logic.search_jobs(
                    title=st.session_state.get("job_title", ""),
                    location=st.session_state.get("job_location", ""),
                    experience=st.session_state.get("job_experience", "Any"),
                    job_type=st.session_state.get("job_type", "Any"),
                )
                st.session_state.job_data = None
                st.session_state.analysis = None

        if st.session_state.jobs:
            st.subheader(f"Results — {len(st.session_state.jobs)} jobs")
            for idx, job in enumerate(st.session_state.jobs):
                if display_job_card(job, str(idx)):
                    st.session_state.selected_job = job
                    st.session_state.job_data = job
                    st.session_state.job_id = db.save_job(job)
                    st.session_state.analysis = None
                    st.rerun()
        else:
            st.info("Enter a title and/or location and click Search.", icon="🔎")

    else:  # Paste mode
        with st.form("pasted_job_form"):
            st.text_input("Job title", placeholder="e.g. Full Stack Developer", key="pasted_job_title")
            st.text_input("Company", placeholder="e.g. Acme Corp", key="pasted_company")
            st.text_area("Paste the full job description here", height=260, key="pasted_job_description")
            submit_paste = st.form_submit_button("🎯 Extract Requirements & Select Job", type="primary")

        if submit_paste:
            desc = st.session_state.get("pasted_job_description", "").strip()
            if not desc:
                st.warning("Please paste a job description first.", icon="\u26a0\ufe0f")
            else:
                with st.spinner("Extracting job requirements with AI\u2026"):
                    try:
                        job_reqs = logic.analyze_job_description(desc)
                        job_data = {
                            # Cap lengths to prevent oversized data in DB
                            "title":           (st.session_state.get("pasted_job_title", "").strip() or "Pasted Job")[:200],
                            "company":         (st.session_state.get("pasted_company", "").strip() or "Unknown Company")[:200],
                            "location":        "",
                            "description":     desc[:15_000],
                            "responsibilities": job_reqs.get("responsibilities", []),
                            "skills":          job_reqs.get("skills", {"must_have": [], "preferred": []}),
                            "source":          "Pasted",
                        }
                        st.session_state.job_data = job_data
                        st.session_state.selected_job = job_data
                        st.session_state.job_id = db.save_job(job_data)
                        st.session_state.analysis = None
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc) if str(exc) else "Failed to extract job requirements. Please try again.")

    # Show currently selected job
    if st.session_state.job_data:
        jd = st.session_state.job_data
        st.success(
            f"✅ **Selected:** {jd.get('title', 'Unknown')} @ {jd.get('company', '')} "
            f"· Source: {jd.get('source', '')}"
        )

st.divider()

# ============================================================================
# STEP 3 — SKILL GAP ANALYSIS
# ============================================================================
st.header("⚡ Step 3 · Skill Gap Analysis")

_ready_for_gap = st.session_state.resume_data and st.session_state.job_data

if not _ready_for_gap:
    missing_parts = []
    if not st.session_state.resume_data:
        missing_parts.append("analyze your resume (Step 1)")
    if not st.session_state.job_data:
        missing_parts.append("select a job (Step 2)")
    st.info(f"Please {' and '.join(missing_parts)} to unlock this step.", icon="🔒")
else:
    if st.button("\u26a1 Run Skill Gap Analysis", type="primary", key="btn_run_gap"):
        with st.spinner("Comparing your skills against the job requirements\u2026"):
            try:
                analysis = logic.compare_skills(
                    st.session_state.resume_data,
                    st.session_state.job_data,
                )
                st.session_state.analysis = analysis
                if st.session_state.resume_id and st.session_state.job_id:
                    st.session_state.analysis_id = db.save_analysis(
                        st.session_state.resume_id,
                        st.session_state.job_id,
                        analysis["match_score"],
                        analysis,
                    )
                st.session_state.roadmap = []
                st.session_state.project = None
                st.rerun()
            except Exception as exc:
                st.error(str(exc) if str(exc) else "Skill gap analysis failed. Please try again.")

    if st.session_state.analysis:
        analysis = st.session_state.analysis
        display_analysis_header(analysis)
        st.write("")
        skill_cols = st.columns(3)
        with skill_cols[0]:
            display_skill_group("Strong skills",   analysis.get("strong_skills",  []), "strong")
        with skill_cols[1]:
            display_skill_group("Partial skills",  analysis.get("partial_skills", []), "partial")
        with skill_cols[2]:
            display_skill_group("Missing skills",  analysis.get("missing_skills", []), "missing")
        gap_col, chart_col = st.columns([1, 2])
        with gap_col:
            display_gap_summary(analysis.get("top_gap"))
        with chart_col:
            display_skill_coverage_chart(analysis.get("skill_coverage"))
    else:
        st.info(
            "Click **Run Skill Gap Analysis** above to compare your resume against the selected job.",
            icon="🎯",
        )

st.divider()

# ============================================================================
# STEP 4 — ROADMAP & PORTFOLIO PROJECT
# ============================================================================
st.header("🧭 Step 4 · Your Personalized Roadmap")

if not st.session_state.analysis:
    st.info("Complete Step 3 (skill gap analysis) to unlock your roadmap.", icon="🔒")
else:
    if st.button("🧭 Generate Roadmap & Portfolio Project", type="primary", key="btn_roadmap"):
        with st.spinner(
            "Building your personalized 4-week roadmap — this may take 15–30 s, "
            "retrying automatically if the model is busy…"
        ):
            try:
                roadmap = logic.generate_roadmap(st.session_state.analysis, st.session_state.job_data)
                project = logic.generate_project(st.session_state.analysis)
                st.session_state.roadmap = roadmap
                st.session_state.project = project
                if st.session_state.analysis_id:
                    db.save_roadmap(st.session_state.analysis_id, roadmap, project)
                st.rerun()
            except Exception as exc:
                st.error(
                    f"Failed to generate roadmap: {exc}\n\n"
                    "The model may be busy — please wait a moment and try again."
                )

    if st.session_state.roadmap:
        target = st.session_state.analysis.get("target_role", "your target role")
        st.success(f"✅ Your 4-week roadmap for **{target}** is ready!")
        for i, week in enumerate(st.session_state.roadmap, start=1):
            display_roadmap_card(week, str(i))

    if st.session_state.project:
        display_project_card(st.session_state.project)

st.divider()

# ============================================================================
# STEP 5 — HISTORY
# ============================================================================
st.header("📊 Previous Analyses")

history = db.get_analysis_history()
if history:
    for index, item in enumerate(history):
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1], vertical_alignment="center")
            c1.markdown(
                f"**{item.get('job_title', 'Unknown role')}**  \n"
                f"{item.get('company', '')}  ·  {item.get('created_at', '')[:10]}"
            )
            c2.metric("Score", f"{item.get('match_score', 0):.1f}%")

            if c3.button("📂 Load", key=f"hist_load_{index}", help="Load this analysis back into Step 3"):
                loaded = db.get_analysis_by_id(item["analysis_id"])
                if loaded and loaded.get("result_json"):
                    st.session_state.analysis = loaded["result_json"]
                    st.toast("✅ Analysis loaded — scroll up to Step 3 to view it.")
                    st.rerun()
                else:
                    st.error("Could not load this analysis.")

            # PDF is generated at render time (pure Python, no AI calls)
            loaded_for_pdf = db.get_analysis_by_id(item["analysis_id"])
            if loaded_for_pdf and loaded_for_pdf.get("result_json"):
                try:
                    pdf_bytes = logic.generate_analysis_pdf(
                        loaded_for_pdf["result_json"],
                        st.session_state.resume_data,
                    )
                    role_slug = (item.get("job_title") or "analysis").replace(" ", "_")
                    date_slug = item.get("created_at", "")[:10]
                    c4.download_button(
                        label="📥 PDF",
                        data=pdf_bytes,
                        file_name=f"careergap_{role_slug}_{date_slug}.pdf",
                        mime="application/pdf",
                        key=f"hist_pdf_{index}",
                        help="Download PDF report",
                    )
                except Exception as pdf_err:
                    c4.caption(f"⚠️ {pdf_err}")
else:
    st.info(
        "Your completed analyses will appear here after you run Step 3.",
        icon="📊",
    )
