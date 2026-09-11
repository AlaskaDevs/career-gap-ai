"""Reusable Streamlit presentation components for CareerGap AI.

These helpers intentionally accept plain dictionaries so the data returned by
future logic and API integrations can be passed in without UI rewrites.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import streamlit as st


def metric_card(label: str, value: str | int | float, delta: str | None = None) -> None:
    """Render one bordered KPI card."""
    st.metric(label, value, delta=delta, border=True)


def display_job_card(job: Mapping[str, Any], key: str) -> bool:
    """Render a job result card and return whether its analysis action was clicked."""
    with st.container(border=True):
        st.subheader(job.get("title", "Untitled role"))
        st.caption(
            f"🏢 {job.get('company', 'Company not provided')}  ·  "
            f"📍 {job.get('location', 'Location not provided')}"
        )
        st.caption(
            f"💼 {job.get('job_type', 'Job type not provided')}  ·  "
            f"👤 {job.get('experience', 'Experience not provided')}"
        )
        st.write(job.get("description", "No job description was provided."))
        action_col, link_col = st.columns([1, 1])
        with action_col:
            analyze_clicked = st.button(
                "🎯 Analyze my skill gap", key=f"analyze_job_{key}", type="primary"
            )
        with link_col:
            url = job.get("url")
            if url:
                st.link_button("🔗 View job", url)
            else:
                st.button("🔗 View job", key=f"view_job_{key}", disabled=True)
                st.caption("Job link will appear with search results.")
    return analyze_clicked


def display_skill(title: str, status: str) -> None:
    """Render a compact skill badge using a native Streamlit status color."""
    colors = {"strong": "green", "partial": "orange", "missing": "red"}
    st.badge(title, color=colors.get(status, "blue"))


def display_skill_group(title: str, skills: Iterable[str], status: str) -> None:
    """Render a bordered group of strong, partial, or missing skills."""
    icon = {"strong": "🟢", "partial": "🟡", "missing": "🔴"}.get(status, "•")
    skills = list(skills)
    with st.container(border=True):
        st.subheader(f"{icon} {title}")
        if skills:
            with st.container(horizontal=True, wrap=True):
                for skill in skills:
                    display_skill(skill, status)
        else:
            st.caption("No skills in this group yet.")


def display_gap_summary(gap: Mapping[str, Any] | None) -> None:
    """Render the highest-priority learning gap when an analysis is available."""
    with st.container(border=True):
        st.markdown("#### 🔥 Top priority gap")
        if not gap:
            st.caption("Your highest-priority gap will appear after an analysis.")
            return
        st.subheader(gap.get("skill", "Priority skill"))
        st.write(gap.get("reason", "Required for the target role."))
        st.caption(f"Priority: {str(gap.get('priority', 'High')).upper()}")


def display_skill_coverage_chart(skill_coverage: Mapping[str, float] | None) -> None:
    """Reserve a chart area; data can later be supplied by logic.py."""
    with st.container(border=True):
        st.subheader("Skill coverage")
        if skill_coverage:
            st.bar_chart(skill_coverage, horizontal=True)
        else:
            st.caption("A skill-coverage bar chart will appear after analysis.")


def display_roadmap_card(week: Mapping[str, Any], key: str) -> None:
    """Render a single weekly roadmap step."""
    with st.container(border=True):
        st.markdown(f"#### Week {week.get('week', key)}")
        st.subheader(week.get("title", "Learning focus"))
        if week.get("hours"):
            st.caption(f"{week['hours']} hours")
        topics = week.get("topics", [])
        if topics:
            st.markdown("**Topics**")
            st.markdown("\n".join(f"- {topic}" for topic in topics))
        if week.get("hands_on"):
            st.markdown("**Hands-on**")
            st.write(week["hands_on"])
        if week.get("outcome"):
            st.markdown("**Outcome**")
            st.write(week["outcome"])


def display_project_card(project: Mapping[str, Any] | None) -> None:
    """Render the recommended portfolio project."""
    with st.container(border=True):
        st.subheader("🚀 Recommended portfolio project")
        if not project:
            st.caption("A project recommendation will appear with your roadmap.")
            return
        st.header(project.get("title", "Portfolio project"))
        if project.get("problem"):
            st.markdown("**Problem**")
            st.write(project["problem"])
        skills = project.get("skills", [])
        if skills:
            st.markdown("**Skills you'll prove**")
            with st.container(horizontal=True, wrap=True):
                for skill in skills:
                    display_skill(skill, "strong")
        details = []
        if project.get("estimated_time"):
            details.append(f"Estimated time: {project['estimated_time']}")
        if project.get("difficulty"):
            details.append(f"Difficulty: {project['difficulty']}")
        if details:
            st.caption("  ·  ".join(details))
        st.button("Copy resume bullet", key="copy_resume_bullet")


def display_analysis_header(analysis: Mapping[str, Any]) -> None:
    """Render the selected role context and headline analysis metrics."""
    details = st.columns(3)
    details[0].markdown(f"**Target role**\n\n{analysis.get('target_role', 'Not set')}")
    details[1].markdown(f"**Company**\n\n{analysis.get('company', 'Not set')}")
    details[2].markdown(f"**Location**\n\n{analysis.get('location', 'Not set')}")

    metrics = st.columns(3)
    with metrics[0]:
        metric_card("Match score", f"{analysis.get('match_score', 0)}%")
    with metrics[1]:
        metric_card("Strong skills", len(analysis.get("strong_skills", [])))
    with metrics[2]:
        metric_card("Skill gaps", len(analysis.get("missing_skills", [])))
