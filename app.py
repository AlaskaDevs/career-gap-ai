"""CareerGap AI UI shell.

Backend services deliberately plug into session state later. No database, API,
file-parsing, or AI work is performed in this module.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui_components import (
    display_analysis_header,
    display_gap_summary,
    display_job_card,
    display_project_card,
    display_roadmap_card,
    display_skill_coverage_chart,
    display_skill_group,
)


st.set_page_config(page_title="CareerGap AI", page_icon="🎯", layout="wide")


def initialise_state() -> None:
    """Create all state contracts expected by future backend integrations."""
    defaults: dict[str, Any] = {
        "resume_text": None,
        "resume_data": None,
        "jobs": [],
        "selected_job": None,
        "job_data": None,
        "analysis": None,
        "roadmap": [],
        "project": None,
        "history": [],
        "ui_notice": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def show_future_integration_notice(action: str) -> None:
    """Keep UI buttons functional without pretending the backend exists."""
    st.session_state.ui_notice = (
        f"{action} is ready to connect. The UI has stored your inputs; "
        "logic.py will provide this action in a later build."
    )


initialise_state()

with st.sidebar:
    st.title("🎯 CareerGap AI")
    st.caption("Your career gap in one place.")
    st.divider()
    st.markdown("**Resume**")
    st.write("✓ Uploaded" if st.session_state.resume_data else "Not uploaded")
    st.markdown("**Target**")
    target = (st.session_state.analysis or {}).get("target_role", "Not selected")
    st.write(target)
    st.markdown("**Match**")
    score = (st.session_state.analysis or {}).get("match_score")
    st.write(f"{score}%" if score is not None else "Not analyzed")
    st.divider()
    st.markdown("**About**")
    st.caption(
        "CareerGap AI compares your skills with real job requirements and "
        "builds a personalized path to close the gap."
    )

st.title("🎯 CareerGap AI")
st.subheader("From Resume → Skill Gap → Learning Roadmap → Career Growth")
st.write(
    "Upload your resume, find a real job, discover your skill gaps, and get a "
    "personalized plan to become job-ready."
)

if st.session_state.ui_notice:
    st.info(st.session_state.ui_notice, icon="ℹ️")

resume_tab, job_tab, roadmap_tab, history_tab = st.tabs(
    ["📄 Resume", "🎯 Job Match", "🧭 Roadmap", "📊 History"]
)

with resume_tab:
    st.header("📄 Upload your resume")
    uploaded_resume = st.file_uploader(
        "Upload resume", type=["pdf", "docx", "txt"], key="resume_upload"
    )
    st.caption("Supported: PDF, DOCX, TXT")
    if uploaded_resume is not None:
        resume_data = {
            "filename": uploaded_resume.name,
            "size": uploaded_resume.size,
            "file_type": uploaded_resume.type,
        }
        if st.session_state.resume_data != resume_data:
            st.session_state.resume_data = resume_data
            st.session_state.resume_text = None
        st.success("Resume uploaded successfully", icon="✅")
        st.write(f"**{uploaded_resume.name}** · {uploaded_resume.size / 1024:.1f} KB")
        st.caption("Text extraction is pending the future resume parser integration.")
        with st.expander("Extracted text preview"):
            if st.session_state.resume_text:
                st.text(st.session_state.resume_text[:2500])
            else:
                st.caption("The extracted text preview will appear here after parsing.")
    else:
        st.info("Upload a resume to begin your job-readiness analysis.", icon="📄")

    if st.button("Analyze resume", type="primary", disabled=uploaded_resume is None):
        show_future_integration_notice("Resume analysis")

with job_tab:
    st.header("🎯 Find your job match")
    input_mode = st.segmented_control(
        "Job input mode",
        ["🔎 Find a Real Job", "📝 Paste Job Description"],
        default="🔎 Find a Real Job",
        key="job_input_mode",
    )

    if input_mode == "🔎 Find a Real Job":
        with st.form("job_search_form"):
            first, second = st.columns(2)
            with first:
                st.text_input("Job title", placeholder="Python Developer", key="job_title")
                st.selectbox("Experience", ["Any", "0–2 years", "3–5 years", "5+ years"], key="job_experience")
            with second:
                st.text_input("Location", placeholder="Hyderabad", key="job_location")
                st.selectbox("Job type", ["Any", "Full-time", "Internship", "Contract"], key="job_type")
            searched = st.form_submit_button("🔎 Search jobs", type="primary")
        if searched:
            show_future_integration_notice("Job search")

        if st.session_state.jobs:
            st.subheader("Search results")
            for index, job in enumerate(st.session_state.jobs):
                if display_job_card(job, str(index)):
                    st.session_state.selected_job = job
                    show_future_integration_notice("Skill-gap analysis")
        else:
            st.info("Search results from the jobs integration will appear here.", icon="🔎")
    else:
        with st.form("pasted_job_form"):
            st.text_input("Job title", key="pasted_job_title")
            st.text_input("Company", key="pasted_company")
            st.text_area("Job description", height=260, key="pasted_job_description")
            analyze_pasted = st.form_submit_button("🎯 Analyze skill gap", type="primary")
        if analyze_pasted:
            st.session_state.job_data = {
                "title": st.session_state.pasted_job_title,
                "company": st.session_state.pasted_company,
                "description": st.session_state.pasted_job_description,
            }
            show_future_integration_notice("Skill-gap analysis")

    st.header("Skill gap analysis")
    analysis = st.session_state.analysis
    if analysis:
        display_analysis_header(analysis)
        st.space("small")
        skill_columns = st.columns(3)
        with skill_columns[0]:
            display_skill_group("Strong skills", analysis.get("strong_skills", []), "strong")
        with skill_columns[1]:
            display_skill_group("Partial skills", analysis.get("partial_skills", []), "partial")
        with skill_columns[2]:
            display_skill_group("Missing skills", analysis.get("missing_skills", []), "missing")
        gap_column, chart_column = st.columns([1, 2])
        with gap_column:
            display_gap_summary(analysis.get("top_gap"))
        with chart_column:
            display_skill_coverage_chart(analysis.get("skill_coverage"))
    else:
        st.info("Choose a job and analyze it to see your match score and skill gaps.", icon="🎯")

with roadmap_tab:
    st.header("🧭 Your personalized roadmap")
    if st.session_state.roadmap:
        for index, week in enumerate(st.session_state.roadmap, start=1):
            display_roadmap_card(week, str(index))
    else:
        st.info("Complete a skill-gap analysis to generate your four-week roadmap.", icon="🧭")
    display_project_card(st.session_state.project)

with history_tab:
    st.header("📊 Previous analyses")
    history = st.session_state.history
    if history:
        for index, item in enumerate(history):
            left, middle, right = st.columns([3, 1, 1], vertical_alignment="center")
            left.write(item.get("target_role", "Untitled analysis"))
            middle.write(f"{item.get('match_score', 0)}%")
            if right.button("View analysis", key=f"history_{index}"):
                st.session_state.analysis = item.get("analysis")
    else:
        st.info("Your completed analyses will be saved here once history is connected.", icon="📊")
