"""SQLite persistence helpers for CareerGap AI.

The module stores flexible backend payloads as JSON while exposing ordinary
Python dictionaries to the rest of the application.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping


DATABASE_PATH = Path(__file__).resolve().parent / "data" / "career_gap.db"


def get_connection() -> sqlite3.Connection:
    """Open a connection to the CareerGap AI database."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the database directory and all tables; safe to call repeatedly."""
    connection = get_connection()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                raw_text TEXT,
                parsed_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                responsibilities TEXT,
                skills TEXT,
                experience TEXT,
                job_type TEXT,
                apply_link TEXT,
                source TEXT,
                raw_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                job_id INTEGER,
                match_score REAL,
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                roadmap_json TEXT,
                project_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def _dump_json(value: Any) -> str | None:
    return None if value is None else json.dumps(value)


def _load_json(value: str | None) -> Any:
    return None if value is None else json.loads(value)


def _as_dict(row: sqlite3.Row | None, json_columns: tuple[str, ...] = ()) -> dict[str, Any] | None:
    if row is None:
        return None
    record = dict(row)
    for column in json_columns:
        record[column] = _load_json(record[column])
    return record


def save_resume(name: str, raw_text: str, parsed_data: Mapping[str, Any] | None = None) -> int:
    """Save a resume and return its new ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO resumes (name, raw_text, parsed_json) VALUES (?, ?, ?)",
            (name, raw_text, _dump_json(parsed_data)),
        )
        return int(cursor.lastrowid)


def get_resume(resume_id: int) -> dict[str, Any] | None:
    """Return one resume, with parsed_json deserialized to a Python object."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    return _as_dict(row, ("parsed_json",))


def save_job(job: Mapping[str, Any]) -> int:
    """Save a normalized job dictionary and return its new ID."""
    raw_payload = job.get("raw_json", job)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO jobs (
                external_id, title, company, location, description,
                responsibilities, skills, experience, job_type, apply_link,
                source, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.get("external_id"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("description"),
                _dump_json(job.get("responsibilities")),
                _dump_json(job.get("skills")),
                job.get("experience"),
                job.get("job_type"),
                job.get("apply_link"),
                job.get("source"),
                _dump_json(raw_payload),
            ),
        )
        return int(cursor.lastrowid)


def get_job(job_id: int) -> dict[str, Any] | None:
    """Return one job, with structured JSON columns deserialized."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _as_dict(row, ("responsibilities", "skills", "raw_json"))


def save_analysis(
    resume_id: int, job_id: int, match_score: float, result_data: Mapping[str, Any]
) -> int:
    """Save an analysis result and return its new ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses (resume_id, job_id, match_score, result_json)
            VALUES (?, ?, ?, ?)
            """,
            (resume_id, job_id, match_score, _dump_json(result_data)),
        )
        return int(cursor.lastrowid)


def get_analysis(analysis_id: int) -> dict[str, Any] | None:
    """Return one analysis and its linked job summary."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT analyses.*, jobs.title AS job_title, jobs.company AS company
            FROM analyses
            LEFT JOIN jobs ON jobs.id = analyses.job_id
            WHERE analyses.id = ?
            """,
            (analysis_id,),
        ).fetchone()
    return _as_dict(row, ("result_json",))


def get_analysis_by_id(analysis_id: int) -> dict[str, Any] | None:
    """Explicit alias for retrieving a single analysis by its ID."""
    return get_analysis(analysis_id)


def save_roadmap(
    analysis_id: int, roadmap_data: Any, project_data: Mapping[str, Any] | None = None
) -> int:
    """Save roadmap and portfolio-project data for an analysis."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO roadmaps (analysis_id, roadmap_json, project_json)
            VALUES (?, ?, ?)
            """,
            (analysis_id, _dump_json(roadmap_data), _dump_json(project_data)),
        )
        return int(cursor.lastrowid)


def get_analysis_history() -> list[dict[str, Any]]:
    """Return compact analysis history for the History tab, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                analyses.id AS analysis_id,
                jobs.title AS job_title,
                jobs.company AS company,
                analyses.match_score AS match_score,
                analyses.created_at AS created_at
            FROM analyses
            LEFT JOIN jobs ON jobs.id = analyses.job_id
            ORDER BY analyses.created_at DESC, analyses.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
