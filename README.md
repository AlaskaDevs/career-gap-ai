# 🎯 CareerGap AI

**🌐 Live Demo:** [CareerGap AI · Streamlit](https://career-gp-ai.streamlit.app/)

> **Upload your resume → pick a real job → discover your exact skill gaps → get a personalized 4-week learning roadmap.**

CareerGap AI is a full-stack AI-powered career tool built for the hackathon. It compares your resume against real job requirements using Google Gemini, calculates a deterministic match score, identifies your strongest and weakest skills, and generates a week-by-week study plan to close the gap — all in a single scrolling page.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 Resume Parsing | Upload PDF, DOCX, or TXT. Extracts name, skills, experience, education, certifications. |
| 🔎 AI Job Search | Enter a job title + location — Gemini generates 3 realistic, relevant job listings. |
| 📝 Paste a Job | Paste any job description — AI extracts must-have and preferred skills automatically. |
| ⚡ Skill Gap Analysis | Semantic matching of your skills vs. the job using Gemini + deterministic scoring formula. |
| 🧭 Personalized Roadmap | 4-week, week-by-week study plan tailored to your exact gaps, not generic advice. |
| 🚀 Portfolio Project | AI recommends one project and writes a ready-to-use STAR-format resume bullet. |
| 📊 History | All analyses stored in SQLite — reload past results or download a PDF report. |
| 📥 PDF Download | One-click report: candidate profile, match score, skill breakdown, top gap. |

---

## 🖥️ Live App Flow

```
Step 1 · Upload & Analyze Resume
        ↓  (Gemini extracts profile)
Step 2 · Select a Target Job
        ↓  (AI search or paste + Gemini extracts requirements)
Step 3 · Skill Gap Analysis
        ↓  (Gemini semantic matching + deterministic score formula)
Step 4 · Roadmap & Portfolio Project
        ↓  (Gemini builds a 4-week plan + project + resume bullet)
Step 5 · History
        ↓  (SQLite stores everything — download PDF any time)
```

The app is a **single scrolling page** — no tabs. Each step unlocks automatically when the previous one is complete.

---

## 📐 How the Match Score Is Calculated

The final percentage is computed by **deterministic Python code**, not by Gemini. Gemini only classifies skills semantically (strong / partial / missing). The math is:

### Step 1 — Semantic classification (Gemini)

Each required skill is classified into one of three buckets:

| Bucket | Meaning |
|---|---|
| **Strong** | Skill is clearly present in the candidate's resume |
| **Partial** | Candidate has adjacent/related experience (e.g. knows MySQL → partial for PostgreSQL) |
| **Missing** | Skill is absent from the resume |

### Step 2 — Weighted scoring (deterministic Python)

Skills are weighted by importance:

| Skill type | Weight |
|---|---|
| Must-have skill | **3 points** |
| Preferred skill | **1 point** |

Credit per classification:

| Classification | Credit |
|---|---|
| Strong | **100%** of weight |
| Partial | **50%** of weight |
| Missing | **0%** |

### Step 3 — Formula

```
total_possible = (count of must-have skills × 3) + (count of preferred skills × 1)

earned = Σ (must-have skills: 3 if strong, 1.5 if partial, 0 if missing)
       + Σ (preferred skills: 1 if strong, 0.5 if partial, 0 if missing)

match_score = round((earned / total_possible) × 100, 1)
match_score = clamp(match_score, 0.0, 100.0)
```

### Example

A job has 4 must-have skills and 2 preferred skills.  
`total_possible = (4 × 3) + (2 × 1) = 14`

The candidate is:
- Strong in 2 must-haves → `2 × 3 = 6`
- Partial in 1 must-have → `1 × 1.5 = 1.5`
- Missing 1 must-have → `0`
- Strong in 1 preferred → `1 × 1 = 1`
- Missing 1 preferred → `0`

`earned = 6 + 1.5 + 1 = 8.5`  
`match_score = round(8.5 / 14 × 100, 1) = **60.7%**`

> The score is always between 0% and 100%, clamped by code. Gemini cannot influence the number — only the classification that feeds into it.

---

## 🗂️ Project Structure

```
career-gap-ai/
├── app.py                  # Main Streamlit app — single-page scrolling UI
├── logic.py                # All AI and business logic (Gemini calls, scoring, PDF)
├── db.py                   # SQLite persistence layer
├── ui_components.py        # Reusable Streamlit UI components
├── seed.py                 # Optional: pre-populate the database with demo data
├── requirements.txt        # Python dependencies
├── .env                    # Your API key (never committed)
├── .env.example            # Template for .env
├── .gitignore              # Protects secrets and build artifacts
└── .streamlit/
    └── config.toml         # Streamlit server config (max upload size = 25 MB)
```

### File Responsibilities

#### `app.py` — UI shell
- Initialises Streamlit session state and SQLite on startup
- Renders the 5-step single-page layout
- Calls `logic.*` functions on button clicks
- Calls `db.*` functions to persist and retrieve data
- Clears downstream state (analysis, roadmap) when the user changes resume or job

#### `logic.py` — Core backend
- `extract_text()` — parses PDF/DOCX/TXT in memory, never writes to disk
- `analyze_resume()` — Gemini call: extracts structured candidate profile
- `search_jobs()` — Gemini call: generates 3 relevant job listings from search criteria
- `analyze_job_description()` — Gemini call: extracts must-have + preferred skills from pasted JD
- `_semantic_match()` — Gemini call: classifies each required skill as strong/partial/missing
- `compare_skills()` — deterministic scoring formula (no AI), returns full analysis dict
- `generate_roadmap()` — Gemini call: 4-week, gap-targeted study plan
- `generate_project()` — Gemini call: portfolio project idea + STAR resume bullet
- `generate_analysis_pdf()` — pure Python PDF using fpdf2, no AI calls
- `_friendly_error()` — converts raw API exceptions to user-safe messages

#### `db.py` — Data persistence
- All queries use parameterized `?` placeholders (SQL injection safe)
- Schema: `resumes`, `jobs`, `analyses`, `roadmaps` tables
- `get_analysis_history()` — JOIN across analyses + jobs, newest first
- `_load_json()` — safely deserializes JSON columns; malformed rows return `None` instead of crashing

#### `ui_components.py` — Reusable UI blocks
- `display_job_card()` — job result card with "Analyze my skill gap" button
- `display_skill_group()` — coloured badge list for strong/partial/missing skills
- `display_analysis_header()` — role, company, location + 3 KPI metrics
- `display_gap_summary()` — top priority gap with reason and priority label
- `display_skill_coverage_chart()` — horizontal bar chart (must-have vs preferred coverage)
- `display_roadmap_card()` — weekly roadmap step with topics, hands-on task, outcome
- `display_project_card()` — portfolio project with resume bullet in copyable code block

#### `seed.py` — Demo data
- Initialises the database and inserts a sample resume record
- Run once manually: `python seed.py`

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **UI** | [Streamlit](https://streamlit.io/) |
| **AI** | [Google Gemini 3.6 Flash](https://ai.google.dev/) via `google-genai` SDK |
| **Database** | SQLite via Python `sqlite3` |
| **PDF Generation** | [fpdf2](https://py-pdf.github.io/fpdf2/) |
| **Resume Parsing** | [PyPDF2](https://pypdf2.readthedocs.io/) + [python-docx](https://python-docx.readthedocs.io/) |
| **Retry Logic** | [tenacity](https://tenacity.readthedocs.io/) — exponential backoff on 503/429 |
| **Environment** | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| **Language** | Python 3.10+ |

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/career-gap-ai.git
cd career-gap-ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your Gemini API key

Copy the example file and add your key:

```bash
cp .env.example .env
```

Open `.env` and set:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Get a free key at: https://aistudio.google.com/app/apikey

### 5. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### 6. (Optional) Seed demo data

```bash
python seed.py
```

---

## 🔒 Security Design

| Area | Approach |
|---|---|
| **API Key** | Loaded from `.env` at runtime; `.gitignore` covers `.env.*`; never logged or displayed |
| **Prompt Injection** | All resume/job text is labelled as untrusted data with explicit separators; model instructed to ignore instruction-like content inside data |
| **SQL Injection** | All SQLite queries use parameterized `?` placeholders — no string interpolation |
| **File Uploads** | In-memory only; extension check + 25 MB server-side limit; malformed documents produce errors, not crashes |
| **SSRF** | `apply_link` is stored as a string for display only; the server never fetches it |
| **AI Output** | Never `eval()`'d or `exec()`'d; always parsed with `json.loads()`; all values type-coerced to `str` |
| **Error Messages** | Raw exceptions are never shown to the user; `_friendly_error()` wraps all AI errors |
| **Stale State** | Uploading a new resume clears all downstream results (analysis, roadmap, project) |

---

## 📊 How the PDF Report Is Generated

When you click **📥 PDF** in the History section:

1. The analysis result is loaded from SQLite (`result_json` column)
2. `generate_analysis_pdf()` in `logic.py` uses **fpdf2** to build the report entirely in Python — no AI calls, no HTML, no JavaScript
3. All text is rendered through fpdf2's safe cell/multi_cell API (latin-1 encoded with replacement for non-ASCII characters)
4. The report includes: candidate name + skills, target role + company, match score (color-coded), strong/partial/missing skill lists, top priority gap
5. Bytes are passed directly to Streamlit's `st.download_button` — the file is never written to disk

---

## 🧠 How Gemini Is Used

The application makes **5 distinct Gemini calls** per full analysis run:

| Call | Function | Output |
|---|---|---|
| 1 | `analyze_resume()` | Candidate profile JSON |
| 2 | `search_jobs()` or `analyze_job_description()` | Job listings JSON or requirements JSON |
| 3 | `_semantic_match()` | Skill classification JSON (strong/partial/missing) |
| 4 | `generate_roadmap()` | 4-week plan JSON |
| 5 | `generate_project()` | Portfolio project + resume bullet JSON |

All calls:
- Request `response_mime_type: "application/json"` for structured output
- Are retried up to **4 times** with exponential backoff on 503/429 errors via `tenacity`
- Use **input length limits** to prevent token overflows (resume: 30K chars, job: 15K chars)
- Have their outputs type-validated and safe-defaulted before use

---

## 📁 Database Schema

```sql
CREATE TABLE resumes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT,           -- sanitized filename
    raw_text    TEXT,           -- extracted resume text
    parsed_json TEXT,           -- Gemini-extracted profile (JSON)
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT,
    company         TEXT,
    location        TEXT,
    description     TEXT,
    responsibilities TEXT,      -- JSON array
    skills          TEXT,       -- JSON: {must_have: [], preferred: []}
    experience      TEXT,
    job_type        TEXT,
    apply_link      TEXT,       -- display only, never server-fetched
    source          TEXT,       -- "AI-Generated" | "Pasted" | "Sample"
    raw_json        TEXT,       -- full job object JSON
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analyses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id   INTEGER,
    job_id      INTEGER,
    match_score REAL,           -- 0.0 – 100.0, deterministic
    result_json TEXT,           -- full analysis result JSON
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roadmaps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id  INTEGER,
    roadmap_json TEXT,          -- 4-week plan JSON array
    project_json TEXT,          -- portfolio project JSON
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🏆 Built For

This project was built as a hackathon submission demonstrating:
- End-to-end Gemini AI integration with structured JSON output
- Deterministic, explainable scoring on top of AI classification
- Secure handling of untrusted file uploads and AI output
- Persistent analysis history with one-click PDF export
- Progressive UX — single scrolling page, no tab-switching required

---

## 📄 License

MIT — see `LICENSE` for details.
