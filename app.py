"""CareerGap AI UI shell."""
from __future__ import annotations
from typing import Any
import streamlit as st
import logging

from ui_components import (
    display_analysis_header,
    display_gap_summary,
    display_job_card,
    display_project_card,
    display_roadmap_card,
    display_skill_coverage_chart,
    display_skill_group,
)
import logic
import db

st.set_page_config(page_title="CareerGap AI", page_icon="🎯", layout="wide")

def initialise_state() -> None:
    """Create all state contracts expected by future backend integrations."""
    defaults: dict[str, Any] = {
        "resume_text": None,
        "resume_data": None,
        "resume_id": None,
        "jobs": [],
        "selected_job": None,
        "job_id": None,
        "job_data": None,
        "analysis": None,
        "analysis_id": None,
        "roadmap": [],
        "project": None,
        "history": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    
    if "db_initialized" not in st.session_state:
        db.init_db()
        st.session_state.db_initialized = True

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
        try:
            if st.session_state.resume_text is None or st.session_state.get('last_uploaded') != uploaded_resume.name:
                with st.spinner("Extracting text..."):
                    st.session_state.resume_text = logic.extract_text(uploaded_resume)
                    st.session_state.last_uploaded = uploaded_resume.name
                    st.session_state.resume_data = None
            st.success("Resume uploaded and extracted successfully", icon="✅")
            st.write(f"**{uploaded_resume.name}** · {uploaded_resume.size / 1024:.1f} KB")
        except Exception as e:
            st.error(f"Error extracting text: {e}")
        
        with st.expander("Extracted text preview"):
            if st.session_state.resume_text:
                st.text(st.session_state.resume_text[:2500])
            else:
                st.caption("The extracted text preview will appear here after parsing.")
    else:
        st.info("Upload a resume to begin your job-readiness analysis.", icon="📄")

    if st.button("Analyze resume", type="primary", disabled=not st.session_state.resume_text):
        with st.spinner("Analyzing resume with AI..."):
            try:
                data = logic.analyze_resume(st.session_state.resume_text)
                st.session_state.resume_data = data
                st.session_state.resume_id = db.save_resume(
                    uploaded_resume.name if uploaded_resume else "Unknown",
                    st.session_state.resume_text,
                    data
                )
                st.success("Resume analyzed successfully!")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                
    if st.session_state.resume_data:
        st.subheader(f"Profile: {st.session_state.resume_data.get('name', 'Unknown')}")
        st.write(f"**Target Roles:** {', '.join(st.session_state.resume_data.get('target_roles', []))}")
        st.write(f"**Skills:** {', '.join(st.session_state.resume_data.get('skills', []))}")

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
                job_title_input = st.text_input("Job title", placeholder="Python Developer", key="job_title")
                experience_input = st.selectbox("Experience", ["Any", "0–2 years", "3–5 years", "5+ years"], key="job_experience")
            with second:
                location_input = st.text_input("Location", placeholder="Hyderabad", key="job_location")
                job_type_input = st.selectbox("Job type", ["Any", "Full-time", "Internship", "Contract"], key="job_type")
            searched = st.form_submit_button("🔎 Search jobs", type="primary")
        if searched:
            with st.spinner("Generating relevant job listings with AI..."):
                st.session_state.jobs = logic.search_jobs(
                    title=st.session_state.get("job_title", ""),
                    location=st.session_state.get("job_location", ""),
                    experience=st.session_state.get("job_experience", "Any"),
                    job_type=st.session_state.get("job_type", "Any"),
                )
                st.session_state.selected_job = None
                st.session_state.job_data = None

        if st.session_state.jobs:
            st.subheader(f"Results ({len(st.session_state.jobs)} jobs found)")
            for index, job in enumerate(st.session_state.jobs):
                clicked = display_job_card(job, str(index))
                if clicked:
                    st.session_state.selected_job = job
                    st.session_state.job_data = job
                    st.session_state.job_id = db.save_job(job)
                    st.session_state.analysis = None  # reset stale analysis
                    st.rerun()
        else:
            st.info("Enter a job title and/or location and click Search to find matching jobs.", icon="🔎")
    else:
        with st.form("pasted_job_form"):
            st.text_input("Job title", placeholder="e.g. Full Stack Developer", key="pasted_job_title")
            st.text_input("Company", placeholder="e.g. Acme Corp", key="pasted_company")
            st.text_area("Paste the full job description here", height=280, key="pasted_job_description")
            analyze_pasted = st.form_submit_button("🎯 Extract Requirements & Select Job", type="primary")
        if analyze_pasted:
            desc = st.session_state.get("pasted_job_description", "").strip()
            if not desc:
                st.warning("Please paste a job description first.", icon="⚠️")
            else:
                with st.spinner("Extracting job requirements with AI..."):
                    try:
                        job_reqs = logic.analyze_job_description(desc)
                        job_data = {
                            "title": st.session_state.get("pasted_job_title", "").strip() or "Pasted Job",
                            "company": st.session_state.get("pasted_company", "").strip() or "Unknown Company",
                            "location": "",
                            "description": desc,
                            "responsibilities": job_reqs.get("responsibilities", []),
                            "skills": job_reqs.get("skills", {"must_have": [], "preferred": []}),
                            "source": "Pasted",
                        }
                        st.session_state.job_data = job_data
                        st.session_state.selected_job = job_data
                        st.session_state.job_id = db.save_job(job_data)
                        st.session_state.analysis = None  # reset stale analysis
                        st.success(f"✅ Job '{job_data['title']}' extracted. Scroll down to run Skill Gap Analysis.")
                    except Exception as e:
                        st.error(f"Failed to extract requirements: {e}")

    st.divider()
    st.header("⚡ Skill Gap Analysis")

    # Show which job is currently selected
    if st.session_state.job_data:
        jd = st.session_state.job_data
        st.success(f"Selected job: **{jd.get('title', 'Unknown')}** @ {jd.get('company', '')} · Source: {jd.get('source', '')}")
    else:
        st.info("Step 1: Select a job above (search or paste a description).", icon="👆")

    if not st.session_state.resume_data:
        st.warning("Step 2: Go to the Resume tab and analyze your resume first.", icon="📄")

    run_disabled = not (st.session_state.resume_data and st.session_state.job_data)
    if st.button("Run Skill Gap Analysis", type="primary", disabled=run_disabled):
        with st.spinner("Comparing your skills against the job requirements..."):
            try:
                analysis = logic.compare_skills(st.session_state.resume_data, st.session_state.job_data)
                st.session_state.analysis = analysis
                if st.session_state.resume_id and st.session_state.job_id:
                    st.session_state.analysis_id = db.save_analysis(
                        st.session_state.resume_id,
                        st.session_state.job_id,
                        analysis["match_score"],
                        analysis
                    )
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    analysis = st.session_state.analysis
    if analysis:
        display_analysis_header(analysis)
        st.write("")
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
    elif not run_disabled:
        st.info("Click **Run Skill Gap Analysis** to compare your resume against the selected job.", icon="🎯")

with roadmap_tab:
    st.header("🧭 Your personalized roadmap")
    if not st.session_state.analysis:
        st.info("Complete a Skill Gap Analysis first, then come back here to generate your roadmap.", icon="⚡")
    else:
        if st.button("Generate Roadmap & Portfolio Project", type="primary"):
            with st.spinner("Building your personalized 4-week roadmap (this may take 15–30s, retrying if needed)..."):
                try:
                    roadmap = logic.generate_roadmap(st.session_state.analysis, st.session_state.job_data)
                    project = logic.generate_project(st.session_state.analysis)
                    st.session_state.roadmap = roadmap
                    st.session_state.project = project
                    if st.session_state.analysis_id:
                        db.save_roadmap(st.session_state.analysis_id, roadmap, project)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate roadmap: {e}\n\nThe model may be busy — please wait a moment and try again.")

        if st.session_state.roadmap:
            st.success(f"Your roadmap for **{st.session_state.analysis.get('target_role', 'your target role')}** is ready!")
            for index, week in enumerate(st.session_state.roadmap, start=1):
                display_roadmap_card(week, str(index))

        if st.session_state.project:
            display_project_card(st.session_state.project)

with history_tab:
    st.header("📊 Previous analyses")
    st.session_state.history = db.get_analysis_history()
    history = st.session_state.history
    if history:
        for index, item in enumerate(history):
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([4, 1, 1, 1], vertical_alignment="center")
                c1.markdown(
                    f"**{item.get('job_title', 'Unknown role')}**  \n"
                    f"{item.get('company', '')}  ·  {item.get('created_at', '')[:10]}"
                )
                c2.metric("Score", f"{item.get('match_score', 0):.1f}%")

                # Load button
                if c3.button("📂 Load", key=f"history_load_{index}", help="Load this analysis into the Job Match tab"):
                    loaded = db.get_analysis_by_id(item["analysis_id"])
                    if loaded and loaded.get("result_json"):
                        st.session_state.analysis = loaded["result_json"]
                        st.toast("✅ Analysis loaded — switch to the Job Match tab to view it.")
                        st.rerun()
                    else:
                        st.error("Could not load this analysis from the database.")

                # PDF download — generate bytes at render time so st.download_button works
                # generate_analysis_pdf is pure Python (no AI calls) so this is fast.
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
                            key=f"history_download_{index}",
                            help="Download PDF report for this analysis",
                        )
                    except Exception as pdf_err:
                        c4.caption(f"⚠️ PDF error: {pdf_err}")
    else:
        st.info(
            "Your completed analyses will be saved here. "
            "Run a Skill Gap Analysis to create the first one.",
            icon="📊",
        )


