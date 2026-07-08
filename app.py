"""
Entry Requirements Checker — lightweight web tool
=================================================
Validates a course page's Entry Requirements against its Qualification
Specification document (and the tracker Excel), using AI comparison.

Workflow
--------
1. Upload the tracker Excel (Course Name / Course URL / Specification
   Document URL / Level / Type — Level & Type are parsed from the course
   name when the columns are absent).
2. Every unique Qualification Specification document is processed ONCE:
   its Entry Requirements are extracted and cached in SQLite. Courses that
   share the same spec URL reuse the cached extraction.
3. Pick a course → Run Check: the course page's Entry Requirements are
   extracted live, compared (AI) against the cached spec + the Excel value.
4. A Pass/Fail report is shown and downloadable as PDF.

Persistence
-----------
Everything the user uploads (courses, cached spec extractions, reports)
is stored in SQLite (er_checker.db) and kept until the user removes it
from the Manage Data page.

Stack:  Python · Streamlit · SQLite · OpenRouter API · reportlab
Run:    streamlit run app.py
"""

import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

# ═══════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════

APP_DIR = Path(__file__).resolve().parent
DB_NAME = "er_checker.db"


def _writable_db_path() -> str:
    """Return a path where SQLite can actually write.

    On hosted platforms (e.g. Streamlit Community Cloud) the deployed
    repo folder — and any er_checker.db committed to it — can be
    read-only, which causes 'attempt to write a readonly database'.
    Try the app folder first, then fall back to the user's home dir and
    the system temp dir. If a bundled (read-only) database exists in
    the repo, seed the writable copy from it so existing data carries
    over. SQLite also needs to create journal files, so both the
    directory and the file must be writable."""
    bundled = APP_DIR / DB_NAME
    for d in (APP_DIR, Path.home() / ".er_checker",
              Path(tempfile.gettempdir()) / "er_checker"):
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".write_test"
            probe.write_text("x")
            probe.unlink()
        except OSError:
            continue  # directory not writable → journal files would fail
        p = d / DB_NAME
        if p.exists() and not os.access(p, os.W_OK):
            try:
                os.chmod(p, 0o664)          # a committed file may be mode 444
            except OSError:
                pass
        if p.exists() and not os.access(p, os.W_OK):
            continue                        # still read-only → next location
        if not p.exists() and bundled.exists() and p != bundled:
            try:
                shutil.copy(bundled, p)     # carry over bundled data
                os.chmod(p, 0o664)
            except OSError:
                pass
        return str(p)
    return str(bundled)                     # last resort


DB_PATH = _writable_db_path()
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"

USER_AGENT = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36")
}

RED = "#D71920"
GREEN = "#1E9E3E"
AMBER = "#C77700"

# ═══════════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════════

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _d(row):
    """sqlite3.Row → plain dict (Streamlit widgets can't deep-copy Row objects)."""
    return dict(row) if row is not None else None


def _ds(rows):
    return [dict(r) for r in rows]


def init_db():
    c = get_conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS courses (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        number        TEXT,
        name          TEXT NOT NULL,
        course_url    TEXT NOT NULL UNIQUE,
        spec_url      TEXT,
        level         TEXT,
        course_type   TEXT,
        excel_entry   TEXT,
        created_at    TEXT,
        updated_at    TEXT
    );
    CREATE TABLE IF NOT EXISTS specs (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        url           TEXT NOT NULL UNIQUE,
        doc_hash      TEXT,
        entry_req     TEXT,
        status        TEXT DEFAULT 'pending',   -- pending | ok | error
        error         TEXT,
        extracted_at  TEXT
    );
    CREATE TABLE IF NOT EXISTS reports (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id     INTEGER NOT NULL,
        result        TEXT,       -- Pass | Fail
        page_entry    TEXT,
        spec_entry    TEXT,
        excel_entry   TEXT,
        issues_json   TEXT,
        corrected     TEXT,
        created_at    TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    """)
    # migration: cache for the formatted (point-by-point, categorised)
    # version of each spec's entry requirements
    try:
        c.execute("ALTER TABLE specs ADD COLUMN entry_req_formatted TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    c.commit()


def setting(key: str, default: str = "") -> str:
    row = get_conn().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    c = get_conn()
    c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
              "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    c.commit()


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── courses ─────────────────────────────────────────────────────────

def parse_level_type(name: str):
    level = course_type = ""
    m = re.search(r"level\s*(\d+)", name or "", re.I)
    if m:
        level = f"Level {m.group(1)}"
    m = re.search(r"\b(extended\s+diploma|combined\s+extended\s+diploma|diploma|"
                  r"certificate|award)\b", name or "", re.I)
    if m:
        course_type = m.group(1).title()
    return level, course_type


def upsert_course(row: dict):
    c = get_conn()
    level, ctype = row.get("level", ""), row.get("course_type", "")
    if not level or not ctype:
        pl, pt = parse_level_type(row.get("name", ""))
        level, ctype = level or pl, ctype or pt
    c.execute("""
        INSERT INTO courses (number, name, course_url, spec_url, level,
                             course_type, excel_entry, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(course_url) DO UPDATE SET
            number=excluded.number, name=excluded.name,
            spec_url=excluded.spec_url, level=excluded.level,
            course_type=excluded.course_type, excel_entry=excluded.excel_entry,
            updated_at=excluded.updated_at
    """, (row.get("number", ""), row["name"], row["course_url"],
          row.get("spec_url", ""), level, ctype,
          row.get("excel_entry", ""), now(), now()))
    c.commit()


def all_courses() -> list:
    return _ds(get_conn().execute(
        "SELECT * FROM courses ORDER BY number, name").fetchall())


def get_course(cid: int):
    return _d(get_conn().execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone())


def delete_course(cid: int):
    c = get_conn()
    c.execute("DELETE FROM reports WHERE course_id=?", (cid,))
    c.execute("DELETE FROM courses WHERE id=?", (cid,))
    c.commit()


def clear_all_data():
    c = get_conn()
    for t in ("reports", "courses", "specs"):
        c.execute(f"DELETE FROM {t}")
    c.commit()


# ── specs cache ─────────────────────────────────────────────────────

def get_spec(url: str):
    return _d(get_conn().execute("SELECT * FROM specs WHERE url=?", (url,)).fetchone())


def ensure_spec_rows():
    """Make sure every distinct spec URL referenced by a course has a cache row."""
    c = get_conn()
    urls = [r["spec_url"] for r in c.execute(
        "SELECT DISTINCT spec_url FROM courses "
        "WHERE spec_url IS NOT NULL AND TRIM(spec_url) != ''")]
    for u in urls:
        c.execute("INSERT OR IGNORE INTO specs (url, status) VALUES (?, 'pending')", (u,))
    c.commit()


def all_specs() -> list:
    return _ds(get_conn().execute("SELECT * FROM specs ORDER BY id").fetchall())


def save_spec(url: str, **fields):
    c = get_conn()
    sets = ", ".join(f"{k}=?" for k in fields)
    c.execute(f"UPDATE specs SET {sets} WHERE url=?", (*fields.values(), url))
    c.commit()


def delete_spec(spec_id: int):
    c = get_conn()
    c.execute("DELETE FROM specs WHERE id=?", (spec_id,))
    c.commit()


# ── reports ─────────────────────────────────────────────────────────

def save_report(course_id: int, result: str, page_entry: str, spec_entry: str,
                excel_entry: str, issues: dict, corrected: str) -> int:
    c = get_conn()
    cur = c.execute("""
        INSERT INTO reports (course_id, result, page_entry, spec_entry,
                             excel_entry, issues_json, corrected, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (course_id, result, page_entry, spec_entry, excel_entry,
          json.dumps(issues, ensure_ascii=False), corrected, now()))
    c.commit()
    return cur.lastrowid


def latest_report(course_id: int):
    return _d(get_conn().execute(
        "SELECT * FROM reports WHERE course_id=? ORDER BY id DESC LIMIT 1",
        (course_id,)).fetchone())


def all_reports() -> list:
    return _ds(get_conn().execute("""
        SELECT r.*, c.name AS course_name, c.course_url, c.spec_url
        FROM reports r JOIN courses c ON c.id = r.course_id
        ORDER BY r.id DESC
    """).fetchall())


def delete_report(report_id: int):
    c = get_conn()
    c.execute("DELETE FROM reports WHERE id=?", (report_id,))
    c.commit()


# ═══════════════════════════════════════════════════════════════════
#  EXTRACTION — spec documents
# ═══════════════════════════════════════════════════════════════════

def _direct_download_url(url: str) -> str:
    """Turn Google Drive share links into direct-download URLs."""
    m = re.search(r"drive\.google\.com/file/d/([^/?#]+)", url or "")
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m = re.search(r"drive\.google\.com/open\?id=([^&#]+)", url or "")
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url


def fetch_spec_bytes(url: str) -> bytes:
    resp = requests.get(_direct_download_url(url), headers=USER_AGENT,
                        timeout=90, allow_redirects=True)
    resp.raise_for_status()
    # Google Drive sometimes interposes a virus-scan confirmation page
    if b"confirm=" in resp.content[:4000] and b"<html" in resp.content[:200].lower():
        m = re.search(rb'href="([^"]*confirm=[^"]*)"', resp.content)
        if m:
            confirm_url = m.group(1).decode().replace("&amp;", "&")
            if confirm_url.startswith("/"):
                confirm_url = "https://drive.google.com" + confirm_url
            resp = requests.get(confirm_url, headers=USER_AGENT, timeout=90)
            resp.raise_for_status()
    return resp.content


def spec_bytes_to_text(data: bytes, url: str = "", max_chars: int = 150000) -> str:
    """PDF / DOCX / HTML → plain text."""
    if data.startswith(b"%PDF"):
        import pdfplumber
        parts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
                if sum(len(p) for p in parts) > max_chars:
                    break
        return "\n".join(parts)[:max_chars]
    if data.startswith(b"PK"):
        from docx import Document
        d = Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        return "\n".join(p for p in parts if p and p.strip())[:max_chars]
    soup = BeautifulSoup(data.decode("utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)[:max_chars]


ENTRY_HEADING = r"entry\s+requirements?|entry\s+criteria|admission\s+requirements?"

# Words/phrases that begin the NEXT section of a spec document.
# NOTE: bare generic words (resources, support, contact, assessment, units…)
# previously matched ordinary body-text lines — PDF extraction preserves the
# document's visual line-wrapping, so a sentence like
#   "…to enable them to access relevant\nresources and complete the unit assignments."
# was mistaken for a "Resources" heading and truncated the section, silently
# dropping everything after it (e.g. the IELTS / CEFR / CAE / PTE list).
_STOP_WORDS = (
    r"method(?:s)?\s+of\s+assessment|assessment(?:\s+(?:overview|methods?|and\s+grading|strategy))?"
    r"|progression(?:\s+(?:opportunities|routes?))?|grading"
    r"|units?(?:\s+(?:overview|summary))?|qualification\s+structure|unit\s+structure"
    r"|guided\s+learning(?:\s+hours)?|total\s+qualification\s+time"
    r"|course\s+content|learning\s+outcomes?|funding|centre(?:\s+requirements?)?"
    r"|appendix(?:\s+\w+)?|introduction|support(?:\s+for\s+learners)?"
    r"|resources?(?:\s+required)?|contact(?:\s+us)?"
    r"|reasonable\s+adjustments|recognition\s+of\s+prior(?:\s+learning)?"
)

# A stop match only counts as a heading when it occupies (almost) the whole
# line: optional section number before, optional colon after, then end of
# line. A wrapped sentence continuing after the word will NOT match.
STOP_HEADINGS = (
    rf"(?:^|\n)[ \t]*(?:\d+(?:\.\d+)*\.?[ \t]+)?"
    rf"(?:{_STOP_WORDS})"
    rf"[ \t]*:?[ \t]*(?=\n|$)"
)


def heuristic_entry_section(text: str, max_chars: int = 6000) -> str:
    """Pull the Entry Requirements section out of a document's text.
    Skips table-of-contents hits (dot leaders / bare page numbers) and,
    when the heading appears more than once, keeps the longest candidate
    (body section) rather than the first (often a passing mention)."""
    if not text:
        return ""
    best = ""
    for m in re.finditer(rf"(?:^|\n)\s*(?:\d+(?:\.\d+)*\.?\s+)?(?:{ENTRY_HEADING})"
                         rf"\s*:?\s*\n?", text, re.I):
        start = m.end()
        stop = re.search(STOP_HEADINGS, text[start:], re.I)
        chunk = text[start:start + stop.start()] if stop else text[start:start + max_chars]
        chunk = re.sub(r"\n{3,}", "\n\n", chunk).strip()[:max_chars]
        head = chunk[:80]
        # TOC lines look like "..... 7" or just a page number
        if re.match(r"^[.·\s]*\d{1,3}\s*$", head) or re.match(r"^\.{4,}", head):
            continue
        if len(chunk) > len(best):
            best = chunk
    return best if len(best) >= 40 else ""


# ═══════════════════════════════════════════════════════════════════
#  EXTRACTION — course pages
# ═══════════════════════════════════════════════════════════════════

def extract_page_entry(url: str) -> tuple:
    """Return (entry_requirements_text, full_page_text). The heading-based
    extraction handles the usual course-page layout; if it fails the caller
    can fall back to sending full_page_text to the AI."""
    resp = requests.get(url, headers=USER_AGENT, timeout=60, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form"]):
        tag.decompose()

    # 1) find a heading whose text is (close to) "Entry Requirements"
    heading = None
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "strong", "b",
                            "button", "a", "span", "div"]):
        t = h.get_text(" ", strip=True)
        if t and len(t) < 60 and re.fullmatch(rf"(?:{ENTRY_HEADING})\s*:?", t, re.I):
            heading = h
            break

    entry = ""
    if heading is not None:
        # accordion/tab layouts: content often lives in the next sibling block
        parts = []
        node = heading
        for _ in range(12):
            node = node.find_next_sibling()
            if node is None:
                break
            t = node.get_text("\n", strip=True)
            if not t:
                continue
            # stop at the next section heading / trailing boilerplate
            if re.match(r"(method(?:s)? of assessment|assessment|course (?:content|curriculum)"
                        r"|qualification|awarding body|career path|who is this|certification"
                        r"|progression|why study|faq|average completion"
                        r"|not sure if this course|speak to an advisor)", t, re.I) and len(t) < 90:
                break
            parts.append(t)
            if sum(len(p) for p in parts) > 3500:
                break
        entry = "\n".join(parts).strip()
        if not entry:  # content nested inside the parent (accordion item)
            parent = heading.find_parent()
            if parent is not None:
                t = parent.get_text("\n", strip=True)
                t = re.sub(rf"^\s*(?:{ENTRY_HEADING})\s*:?\s*", "", t, flags=re.I)
                entry = t.strip()[:4000]

    main = soup.find("main") or soup.find("article") or soup.body or soup
    full_text = re.sub(r"\n{3,}", "\n\n", main.get_text("\n", strip=True))[:14000]

    if not entry:  # 2) heuristic on the flattened page text
        entry = heuristic_entry_section(full_text)

    # trim marketing boilerplate that trails the requirements list
    entry = re.split(r"not sure if this course|speak to an advisor"
                     r"|average completion timeframe|\b0\d{2}[- ]\d{4}[- ]\d{4}\b",
                     entry, flags=re.I)[0].strip()
    return entry[:4000], full_text


# ═══════════════════════════════════════════════════════════════════
#  AI (OpenRouter)
# ═══════════════════════════════════════════════════════════════════

# US-based OpenRouter providers that host DeepSeek models. When the
# "US-hosted providers only" setting is on, requests are routed to these
# hosts and never to DeepSeek's own (China-based) first-party API.
US_PROVIDER_ORDER = ["fireworks", "together", "deepinfra"]


def call_ai(prompt: str, system: str, temperature: float = 0.0) -> str:
    api_key = setting("api_key")
    if not api_key:
        raise RuntimeError("No OpenRouter API key set — add it in the sidebar.")
    payload = {
        "model": setting("model", DEFAULT_MODEL),
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if setting("us_only", "1") == "1":
        payload["provider"] = {
            "order": US_PROVIDER_ORDER,      # prefer these US hosts, in order
            "ignore": ["deepseek"],          # never DeepSeek's own API
            "allow_fallbacks": True,         # other OpenRouter hosts as backup
        }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Entry Requirements Checker",
        },
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_json_reply(raw: str) -> dict:
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.S)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            return json.loads(m.group(0))
        raise


AI_EXTRACT_SYSTEM = ("You extract sections from documents. "
                     "Reply ONLY with valid JSON — no markdown, no commentary.")

AI_EXTRACT_PROMPT = """From the text below, extract the ENTRY REQUIREMENTS section verbatim (fix broken line-wrapping but do not reword). If it is genuinely absent, use an empty string.

Reply with EXACTLY this JSON: {{"entry_requirements": "..."}}

TEXT:
{text}
"""


def ai_extract_entry(text: str) -> str:
    raw = call_ai(AI_EXTRACT_PROMPT.format(text=text[:14000]), AI_EXTRACT_SYSTEM)
    return parse_json_reply(raw).get("entry_requirements", "").strip()


AI_COMPARE_SYSTEM = (
    "You are a meticulous quality auditor for a UK college. You compare a course "
    "page's Entry Requirements against the awarding body's Qualification "
    "Specification and the internal tracker sheet. Reply ONLY with valid JSON — "
    "no markdown fences, no commentary."
)

AI_COMPARE_PROMPT = """Course: "{name}"

Compare the Entry Requirements from the three sources below. The QUALIFICATION SPECIFICATION is the authoritative source of truth; the COURSE PAGE is what students see and must faithfully reflect the specification; the EXCEL TRACKER is the internal record.

Identify:
1. Whether the course page's entry requirements match the specification (and whether the Excel tracker matches too).
2. Missing requirements — present in the specification but absent from the course page.
3. Incorrect requirements — present on the course page but wrong or absent per the specification (e.g. wrong age, wrong grades, wrong test scores).
4. Wording differences that change the meaning (e.g. "must" vs "recommended", "and" vs "or").
5. Grammar and spelling issues on the course page.
6. Suggested corrected Entry Requirements for the course page. This MUST be the COMPLETE set of entry requirements from the QUALIFICATION SPECIFICATION: list EVERY requirement point by point (one per line, each line starting with "- "), using the specification's wording exactly as written. Do NOT summarise, shorten, merge or omit ANY requirement from the specification.

Minor stylistic rephrasing that does NOT change meaning is acceptable and should NOT cause a fail. Fail only for missing requirements, incorrect requirements, or meaning-changing wording. Grammar/spelling issues alone do not fail a course, but list them.

Reply with EXACTLY this JSON:
{{
  "result": "Pass" or "Fail",
  "matches_specification": true/false,
  "matches_excel": true/false,
  "missing_requirements": ["..."],
  "incorrect_requirements": ["..."],
  "wording_differences": ["..."],
  "grammar_spelling": ["..."],
  "summary": "1-3 sentence overall verdict",
  "corrected_entry_requirements": "- requirement 1\\n- requirement 2\\n- ... (every requirement from the specification, verbatim, none omitted)"
}}

COURSE PAGE ENTRY REQUIREMENTS:
{page}

QUALIFICATION SPECIFICATION ENTRY REQUIREMENTS:
{spec}

EXCEL TRACKER ENTRY REQUIREMENTS:
{excel}
"""


def ai_compare(name: str, page: str, spec: str, excel: str) -> dict:
    prompt = AI_COMPARE_PROMPT.format(
        name=name,
        page=page.strip() or "(not found on the course page)",
        spec=spec.strip() or "(not available)",
        excel=excel.strip() or "(not provided)",
    )
    return parse_json_reply(call_ai(prompt, AI_COMPARE_SYSTEM))


# ═══════════════════════════════════════════════════════════════════
#  SUGGESTED CORRECTED ENTRY REQUIREMENTS
# ═══════════════════════════════════════════════════════════════════
# The suggested output must be the COMPLETE set of entry requirements
# from the qualification specification, listed point by point with the
# specification's wording preserved verbatim. It is therefore built
# deterministically from the cached spec extraction rather than from
# the AI's (potentially summarised) suggestion — the AI text is only
# used as a fallback when no specification is available.

_BULLET_MARK = re.compile(
    r"^\s*(?:[-–—•▪●○◦*]|\d{1,2}[.)]|[a-zA-Z][.)]|o(?=\s))\s*")


def spec_to_points(spec: str) -> str:
    """Format the specification's Entry Requirements as a point-by-point
    list ('- ' per line), keeping every requirement and its exact wording.
    Only layout is normalised: PDF line-wrapping is re-joined and bullet
    glyphs are unified — no words are added, changed or removed."""
    text = (spec or "").strip()
    if not text:
        return ""

    # 1) merge PDF/DOCX line-wrapping back into logical lines: a line
    #    continues the previous one unless it starts with a bullet/number
    #    marker or the previous line already ended a sentence/clause.
    logical = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        starts_new = bool(_BULLET_MARK.match(line))
        if logical and not starts_new and not re.search(r"[.:;!?]$", logical[-1]):
            logical[-1] += " " + line
        else:
            logical.append(line)

    # 2) strip the bullet glyph/number — the wording itself is untouched
    points = [p for p in (_BULLET_MARK.sub("", ln).strip() for ln in logical) if p]

    # 3) a single unbroken prose block still needs to read point by point:
    #    split on sentence boundaries (wording remains verbatim)
    if len(points) == 1 and len(points[0]) > 200:
        points = [s.strip() for s in
                  re.split(r"(?<=[.;])\s+(?=[A-Z(])", points[0]) if s.strip()]

    return "\n".join(f"- {p}" for p in points)


def build_corrected_entry(spec_entry: str, ai_corrected: str) -> str:
    """The suggested corrected Entry Requirements shown to the user.
    Specification available → the full spec list (nothing omitted).
    No specification → fall back to the AI suggestion."""
    if (spec_entry or "").strip():
        return spec_to_points(spec_entry)
    return (ai_corrected or "").strip()


# ── AI formatting into the categorised, point-by-point layout ────────

AI_FORMAT_SYSTEM = (
    "You format the Entry Requirements of UK qualification specifications. "
    "Reply ONLY with the formatted text — no JSON, no code fences, no commentary "
    "before or after."
)

AI_FORMAT_PROMPT = """Reformat the ENTRY REQUIREMENTS below into the exact layout of this example (structure and style only — the CONTENT must come solely from the text provided):

Based on the provided document, the entry requirements for the {name} are as follows:

* Age Requirement: These qualifications are designed for learners who are typically aged 16+.
* General Access Policy: ATHE's policy ensures that the qualifications should be available to everyone capable of reaching the required standards, free from barriers to access and progression, and with equal opportunities for all.
* Typical Entry Profile for Recent Learners: For learners who have recently been in education or training, the entry profile is likely to include one of the following:
    * 5 or more GCSEs at grades 4 and above
    * Other related level 2 subjects
* English Language Proficiency: Learners must have an appropriate standard of English to access resources and complete assignments. For those whose first language is not English, the recommended standards are:
    * IELTS 5.5
    * Common European Framework of Reference (CEFR) B2

RULES — follow ALL of them:
1. Start with exactly: "Based on the provided document, the entry requirements for the {name} are as follows:"
2. Include EVERY requirement from the source text. Do NOT omit, merge, shorten or summarise anything. Every age limit, qualification, grade, test name, score, policy statement and centre obligation in the source MUST appear in the output.
3. Keep the specification's wording faithful — you may only add the short category labels (e.g. "Age Requirement:", "English Language Proficiency:") and adjust joining words needed by the layout. Never change numbers, grades, scores or test names.
4. One "* " bullet per requirement category, starting with a bold-free short label followed by a colon.
5. Where the source lists alternatives or multiple items (e.g. GCSE options, English tests), put each item on its own nested bullet indented with 4 spaces: "    * item".
6. Do not invent requirements that are not in the source text.
7. EXCLUDE anything about "Reasonable Adjustments" and "Special Considerations" — do not output that section or any of its content, even if it appears in the source text.

ENTRY REQUIREMENTS (source text):
{spec}
"""


# Sections that must never appear in the suggested output
_EXCLUDED_SECTIONS = re.compile(
    r"reasonable\s+adjustments?|special\s+considerations?", re.I)


def strip_excluded_sections(text: str) -> str:
    """Remove excluded sections (e.g. 'Reasonable Adjustments and Special
    Considerations') from the formatted output, including their nested
    sub-bullets. A top-level bullet whose label matches is dropped together
    with every indented line that follows it."""
    out, skipping = [], False
    for ln in (text or "").split("\n"):
        stripped = ln.lstrip()
        indent = len(ln) - len(stripped)
        is_bullet = stripped.startswith(("* ", "- ", "• "))
        top_level = (is_bullet and indent == 0) or (not is_bullet and stripped)
        if top_level:
            skipping = bool(_EXCLUDED_SECTIONS.search(stripped[:80]))
        if not skipping:
            out.append(ln)
    # tidy runs of blank lines left behind
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def format_spec_entry(qual_name: str, spec_entry: str) -> str:
    """AI-format the spec's Entry Requirements into the categorised
    point-by-point layout. Falls back to the deterministic list if the
    AI reply fails or looks incomplete (guarding against omissions)."""
    fallback = strip_excluded_sections(spec_to_points(spec_entry))
    try:
        out = call_ai(AI_FORMAT_PROMPT.format(name=qual_name, spec=spec_entry),
                      AI_FORMAT_SYSTEM).strip()
        out = re.sub(r"^```[a-z]*\s*|\s*```$", "", out, flags=re.S).strip()
        out = strip_excluded_sections(out)
        # completeness guard: a faithful reformat of the full spec cannot be
        # much shorter than the source — if it is, requirements were dropped
        # (the excluded section is discounted from the source length first)
        src = strip_excluded_sections(spec_to_points(spec_entry))
        if out and len(out) >= 0.6 * len(src):
            return out
    except Exception:
        pass
    return fallback


def get_or_build_formatted(spec_url: str, qual_name: str, spec_entry: str) -> str:
    """Formatted spec requirements, cached per specification document.
    Cached values are passed through the exclusion filter so entries
    formatted before an exclusion rule was added are cleaned up too."""
    row = get_spec(spec_url) if spec_url else None
    if row and row.get("entry_req_formatted"):
        return strip_excluded_sections(row["entry_req_formatted"])
    formatted = format_spec_entry(qual_name, spec_entry)
    if row and formatted:
        save_spec(spec_url, entry_req_formatted=formatted)
    return formatted


# ═══════════════════════════════════════════════════════════════════
#  SPEC PROCESSING (once per unique document)
# ═══════════════════════════════════════════════════════════════════

def process_spec(url: str, force: bool = False, use_ai_fallback: bool = True) -> dict:
    """Extract & cache the Entry Requirements of one spec document.
    Skips work when the document is unchanged (hash match) unless force=True."""
    existing = get_spec(url)
    try:
        data = fetch_spec_bytes(url)
        doc_hash = hashlib.sha256(data).hexdigest()
        if (existing and existing["status"] == "ok" and not force
                and existing["doc_hash"] == doc_hash and existing["entry_req"]):
            return {"skipped": True, "status": "ok"}
        text = spec_bytes_to_text(data, url)
        entry = heuristic_entry_section(text)
        if use_ai_fallback and setting("api_key"):
            if not entry or len(entry) < 40:
                # heuristic found nothing — let the AI search the document
                entry = ai_extract_entry(text)
            else:
                # heuristic found a section — cross-check it against an AI
                # extraction of the surrounding window; keep the more
                # complete of the two (guards against silent truncation)
                pos = text.lower().find(entry[:60].lower())
                window = text[max(0, pos - 1000):pos + len(entry) + 6000] if pos != -1 else text
                ai_entry = ai_extract_entry(window)
                if len(ai_entry) > len(entry):
                    entry = ai_entry
        if not entry:
            raise RuntimeError("Entry Requirements section not found in the document.")
        save_spec(url, doc_hash=doc_hash, entry_req=entry, status="ok",
                  error="", extracted_at=now(), entry_req_formatted="")
        return {"skipped": False, "status": "ok"}
    except Exception as e:
        save_spec(url, status="error", error=str(e)[:500], extracted_at=now())
        return {"skipped": False, "status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════
#  PDF REPORT
# ═══════════════════════════════════════════════════════════════════

def build_pdf(course, report) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle)

    issues = json.loads(report["issues_json"] or "{}")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                            topMargin=16*mm, bottomMargin=16*mm,
                            title="Entry Requirements Validation Report")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=16, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12,
                        textColor=colors.HexColor("#333333"), spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5, leading=13)

    def esc(t):
        return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") \
                        .replace("\n", "<br/>")

    story = [Paragraph("Entry Requirements Validation Report", h1)]

    result = report["result"] or "—"
    result_color = GREEN if result == "Pass" else RED
    meta = Table([
        ["Course Name", course["name"]],
        ["Course URL", course["course_url"]],
        ["Qualification Specification", course["spec_url"] or "—"],
        ["Checked", report["created_at"]],
        ["Validation Result", result],
    ], colWidths=[45*mm, 130*mm])
    meta.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
        ("TEXTCOLOR", (1, 4), (1, 4), colors.HexColor(result_color)),
        ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
    ]))
    story += [meta, Spacer(1, 4)]

    if issues.get("summary"):
        story += [Paragraph("Summary", h2), Paragraph(esc(issues["summary"]), body)]

    story += [Paragraph("Entry Requirements — Course Page", h2),
              Paragraph(esc(report["page_entry"]) or "—", body),
              Paragraph("Entry Requirements — Qualification Specification", h2),
              Paragraph(esc(report["spec_entry"]) or "—", body),
              Paragraph("Entry Requirements — Excel Tracker", h2),
              Paragraph(esc(report["excel_entry"]) or "—", body)]

    def issue_block(title, key):
        items = issues.get(key) or []
        story.append(Paragraph(title, h2))
        if items:
            for i, it in enumerate(items, 1):
                story.append(Paragraph(f"{i}. {esc(it)}", body))
        else:
            story.append(Paragraph("None", body))

    issue_block("Missing Requirements", "missing_requirements")
    issue_block("Incorrect Requirements", "incorrect_requirements")
    issue_block("Wording Differences (meaning-changing)", "wording_differences")
    issue_block("Grammar & Spelling Issues", "grammar_spelling")

    corrected = strip_excluded_sections(
        (report["corrected"] or "").strip()
        or build_corrected_entry(report["spec_entry"], ""))
    story += [Paragraph("Suggested Corrected Entry Requirements "
                        "(complete set from the qualification specification)", h2),
              Paragraph(esc(corrected) or "—", body)]

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════
#  EXCEL IMPORT
# ═══════════════════════════════════════════════════════════════════

COLUMN_ALIASES = {
    "number": ["number", "no", "id", "category id"],
    "name": ["course name", "name", "course"],
    "course_url": ["course url", "url", "page url", "course link"],
    "spec_url": ["specification document", "qualification specification document url",
                 "spec url", "specification url", "qualification specification",
                 "spec document", "specification document url"],
    "level": ["level"],
    "course_type": ["type", "course type"],
    "excel_entry": ["entry requirements", "entry requirement"],
}


def import_excel(file) -> dict:
    df = pd.read_excel(file)
    cols = {str(c).strip().lower(): c for c in df.columns}

    def col(key):
        for alias in COLUMN_ALIASES[key]:
            if alias in cols:
                return cols[alias]
        return None

    name_c, url_c = col("name"), col("course_url")
    if name_c is None or url_c is None:
        raise ValueError("The Excel file must contain 'Course Name' and "
                         "'Course URL' columns.")
    mapping = {k: col(k) for k in COLUMN_ALIASES}
    imported = skipped = 0
    for _, r in df.iterrows():
        name = str(r.get(name_c, "") or "").strip()
        url = str(r.get(url_c, "") or "").strip()
        if not name or not url or not url.lower().startswith("http"):
            skipped += 1
            continue
        row = {"name": name, "course_url": url}
        for k in ("number", "spec_url", "level", "course_type", "excel_entry"):
            c = mapping.get(k)
            v = r.get(c, "") if c is not None else ""
            row[k] = "" if pd.isna(v) else str(v).strip()
        upsert_course(row)
        imported += 1
    ensure_spec_rows()
    return {"imported": imported, "skipped": skipped}


# ═══════════════════════════════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Entry Requirements Checker", page_icon="✅",
                   layout="wide")
init_db()

st.sidebar.title("✅ Entry Requirements Checker")
page = st.sidebar.radio("Navigate", ["📥 Upload & Specs", "▶️ Run Check",
                                     "📄 Reports", "🗂️ Manage Data"])

with st.sidebar.expander("⚙️ AI Settings", expanded=not setting("api_key")):
    key_in = st.text_input("OpenRouter API key", value=setting("api_key"),
                           type="password")
    model_in = st.text_input("Model", value=setting("model", DEFAULT_MODEL))
    us_in = st.checkbox("US-hosted providers only",
                        value=setting("us_only", "1") == "1",
                        help="Route DeepSeek requests to US hosts "
                             "(Fireworks, Together, DeepInfra) and never to "
                             "DeepSeek's own API.")
    if st.button("Save settings"):
        set_setting("api_key", key_in.strip())
        set_setting("model", model_in.strip() or DEFAULT_MODEL)
        set_setting("us_only", "1" if us_in else "0")
        st.success("Saved.")


def badge(result: str) -> str:
    color = GREEN if result == "Pass" else RED
    return (f"<span style='background:{color};color:#fff;padding:3px 14px;"
            f"border-radius:12px;font-weight:700'>{result}</span>")


# ── PAGE: Upload & Specs ────────────────────────────────────────────
if page == "📥 Upload & Specs":
    st.header("Upload Tracker Excel")
    st.caption("Columns used: Course Name · Course URL · Specification Document · "
               "Level · Type · Entry Requirements. Level/Type are parsed from the "
               "course name when the columns are missing. Uploaded data is stored "
               "until you remove it in 🗂️ Manage Data.")
    up = st.file_uploader("Excel file (.xlsx)", type=["xlsx", "xlsm", "xls"])
    if up is not None and st.button("Import courses", type="primary"):
        try:
            res = import_excel(up)
            st.success(f"Imported/updated {res['imported']} courses "
                       f"({res['skipped']} rows skipped).")
        except Exception as e:
            st.error(f"Import failed: {e}")

    courses = all_courses()
    if courses:
        st.subheader(f"Courses stored ({len(courses)})")
        st.dataframe(pd.DataFrame(
            [{"Number": c["number"], "Course Name": c["name"],
              "Level": c["level"], "Type": c["course_type"],
              "Spec URL": c["spec_url"]} for c in courses]),
            use_container_width=True, height=280)

    st.divider()
    st.header("Qualification Specification Documents")
    ensure_spec_rows()
    specs = all_specs()
    if not specs:
        st.info("Import the Excel first — unique specification documents will be "
                "listed here.")
    else:
        pending = [s for s in specs if s["status"] != "ok"]
        st.caption(f"{len(specs)} unique documents · "
                   f"{len(specs) - len(pending)} extracted · {len(pending)} pending/error. "
                   "Each document is processed once and cached; it is only "
                   "re-extracted if the file changes or you force it.")
        c1, c2 = st.columns(2)
        run_pending = c1.button("Process pending documents", type="primary",
                                disabled=not pending)
        run_all = c2.button("Re-check all (skips unchanged files)")
        if run_pending or run_all:
            targets = specs if run_all else pending
            prog = st.progress(0.0)
            status_box = st.empty()
            done = 0
            for s in targets:
                status_box.write(f"Processing: {s['url']}")
                process_spec(s["url"])
                done += 1
                prog.progress(done / len(targets))
            status_box.empty()
            st.rerun()

        for s in all_specs():
            n_courses = get_conn().execute(
                "SELECT COUNT(*) c FROM courses WHERE spec_url=?",
                (s["url"],)).fetchone()["c"]
            icon = {"ok": "🟢", "error": "🔴"}.get(s["status"], "⚪")
            with st.expander(f"{icon} {s['url']}  ·  used by {n_courses} course(s)"):
                if s["status"] == "error":
                    st.error(s["error"])
                edited = st.text_area("Entry Requirements (cached — editable)",
                                      value=s["entry_req"] or "", height=160,
                                      key=f"spec_{s['id']}")
                b1, b2 = st.columns(2)
                if b1.button("Save edits", key=f"save_{s['id']}"):
                    save_spec(s["url"], entry_req=edited, status="ok", error="",
                              extracted_at=now(), entry_req_formatted="")
                    st.success("Saved.")
                if b2.button("Force re-extract", key=f"re_{s['id']}"):
                    with st.spinner("Re-extracting…"):
                        process_spec(s["url"], force=True)
                    st.rerun()


# ── PAGE: Run Check ─────────────────────────────────────────────────
elif page == "▶️ Run Check":
    st.header("Run Check")
    courses = all_courses()
    if not courses:
        st.info("Upload the tracker Excel first (📥 Upload & Specs).")
        st.stop()

    levels = sorted({c["level"] for c in courses if c["level"]})
    types = sorted({c["course_type"] for c in courses if c["course_type"]})
    f1, f2, f3 = st.columns([1, 1, 2])
    f_level = f1.selectbox("Level", ["All"] + levels)
    f_type = f2.selectbox("Type", ["All"] + types)
    f_text = f3.text_input("Search course name")

    filtered = [c for c in courses
                if (f_level == "All" or c["level"] == f_level)
                and (f_type == "All" or c["course_type"] == f_type)
                and (f_text.lower() in c["name"].lower())]
    if not filtered:
        st.warning("No courses match the filters.")
        st.stop()

    sel = st.selectbox("Course", filtered,
                       format_func=lambda c: f"{c['number']} — {c['name']}"
                       if c["number"] else c["name"])
    course = get_course(sel["id"])

    st.markdown(f"**Course URL:** {course['course_url']}  \n"
                f"**Specification:** {course['spec_url'] or '—'}")

    spec_row = get_spec(course["spec_url"]) if course["spec_url"] else None
    spec_ready = bool(spec_row and spec_row["status"] == "ok" and spec_row["entry_req"])
    if course["spec_url"] and not spec_ready:
        st.warning("This course's specification hasn't been extracted yet — it will "
                   "be processed automatically when you run the check (and cached "
                   "for every course sharing it).")
    elif not course["spec_url"]:
        st.warning("No specification document URL for this course — the check will "
                   "compare the page against the Excel tracker only.")

    if st.button("Run Check", type="primary"):
        if not setting("api_key"):
            st.error("Add your OpenRouter API key in the sidebar first.")
            st.stop()
        try:
            with st.spinner("1/3 Reading course page…"):
                page_entry, full_text = extract_page_entry(course["course_url"])
                if not page_entry:
                    page_entry = ai_extract_entry(full_text)
            spec_entry = ""
            if course["spec_url"]:
                with st.spinner("2/3 Loading specification (cached when possible)…"):
                    if not spec_ready:
                        process_spec(course["spec_url"])
                    spec_row = get_spec(course["spec_url"])
                    if spec_row and spec_row["status"] == "ok":
                        spec_entry = spec_row["entry_req"] or ""
                    else:
                        st.warning("Specification could not be extracted: "
                                   f"{spec_row['error'] if spec_row else 'unknown error'}")
            with st.spinner("3/3 Comparing & formatting with AI…"):
                verdict = ai_compare(course["name"], page_entry, spec_entry,
                                     course["excel_entry"] or "")
                if spec_entry.strip():
                    corrected = get_or_build_formatted(
                        course["spec_url"], course["name"], spec_entry)
                else:
                    corrected = verdict.get("corrected_entry_requirements", "")
            result = "Pass" if str(verdict.get("result", "")).lower() == "pass" else "Fail"
            save_report(course["id"], result, page_entry, spec_entry,
                        course["excel_entry"] or "", verdict, corrected)
            st.success("Check complete.")
        except Exception as e:
            st.error(f"Check failed: {e}")

    report = latest_report(course["id"])
    if report:
        issues = json.loads(report["issues_json"] or "{}")
        st.divider()
        st.subheader("Validation Report")
        st.markdown(f"**Result:** {badge(report['result'])} &nbsp;·&nbsp; "
                    f"checked {report['created_at']}", unsafe_allow_html=True)
        if issues.get("summary"):
            st.markdown(f"> {issues['summary']}")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Course Page**")
            st.text_area("page", report["page_entry"] or "—", height=220,
                         label_visibility="collapsed", disabled=True)
        with c2:
            st.markdown("**Qualification Specification**")
            st.text_area("spec", report["spec_entry"] or "—", height=220,
                         label_visibility="collapsed", disabled=True)
        with c3:
            st.markdown("**Excel Tracker**")
            st.text_area("excel", report["excel_entry"] or "—", height=220,
                         label_visibility="collapsed", disabled=True)

        def show_issues(title, key, color):
            items = issues.get(key) or []
            st.markdown(f"**{title}** "
                        f"<span style='color:{color}'>({len(items)})</span>",
                        unsafe_allow_html=True)
            if items:
                for it in items:
                    st.markdown(f"- {it}")
            else:
                st.caption("None")

        i1, i2 = st.columns(2)
        with i1:
            show_issues("Missing Requirements", "missing_requirements", RED)
            show_issues("Incorrect Requirements", "incorrect_requirements", RED)
        with i2:
            show_issues("Wording Differences", "wording_differences", AMBER)
            show_issues("Grammar & Spelling", "grammar_spelling", AMBER)

        st.markdown("**Suggested Corrected Entry Requirements**")
        st.caption("Complete set of entry requirements from the qualification "
                   "specification, point by point — compare directly with the "
                   "course page requirements above.")
        corrected_txt = strip_excluded_sections(
            (report["corrected"] or "").strip()
            or build_corrected_entry(report["spec_entry"], ""))
        st.markdown(corrected_txt or "—")

        pdf = build_pdf(course, report)
        st.download_button("⬇️ Download Report (PDF)", data=pdf,
                           file_name=f"ER_Report_{re.sub(r'[^A-Za-z0-9]+', '_', course['name'])[:60]}.pdf",
                           mime="application/pdf")


# ── PAGE: Reports ───────────────────────────────────────────────────
elif page == "📄 Reports":
    st.header("All Reports")
    reports = all_reports()
    if not reports:
        st.info("No reports yet — run a check first.")
    for r in reports:
        icon = "🟢" if r["result"] == "Pass" else "🔴"
        with st.expander(f"{icon} {r['result']} · {r['course_name']} · {r['created_at']}"):
            issues = json.loads(r["issues_json"] or "{}")
            if issues.get("summary"):
                st.markdown(f"> {issues['summary']}")
            course = get_course(r["course_id"])
            if course:
                pdf = build_pdf(course, r)
                st.download_button("⬇️ Download PDF", data=pdf,
                                   file_name=f"ER_Report_{r['id']}.pdf",
                                   mime="application/pdf", key=f"dl_{r['id']}")
            if st.button("Delete report", key=f"delrep_{r['id']}"):
                delete_report(r["id"])
                st.rerun()


# ── PAGE: Manage Data ───────────────────────────────────────────────
else:
    st.header("Manage Stored Data")
    st.caption("Everything you upload is kept in the local database "
               f"(`{DB_PATH}`) until you remove it here.")

    st.subheader("Courses")
    for c in all_courses():
        col1, col2 = st.columns([6, 1])
        col1.markdown(f"**{c['number']} — {c['name']}**  \n{c['course_url']}")
        if col2.button("🗑️ Remove", key=f"delc_{c['id']}"):
            delete_course(c["id"])
            st.rerun()

    st.subheader("Cached Specification Extractions")
    for s in all_specs():
        col1, col2 = st.columns([6, 1])
        col1.markdown(f"{'🟢' if s['status'] == 'ok' else '🔴'} {s['url']}")
        if col2.button("🗑️ Remove", key=f"dels_{s['id']}"):
            delete_spec(s["id"])
            st.rerun()

    st.divider()
    st.subheader("Danger zone")
    confirm = st.checkbox("I understand this deletes ALL courses, cached specs "
                          "and reports.")
    if st.button("🗑️ Clear all data", type="primary", disabled=not confirm):
        clear_all_data()
        st.success("All data removed.")
        st.rerun()