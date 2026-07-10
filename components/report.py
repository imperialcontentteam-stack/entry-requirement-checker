"""Reports dashboard: summary cards and search / filter / sort controls.
Pure presentation + list shaping — no database or AI logic."""

import json

import streamlit as st

from . import cards


def _issues(r, key):
    try:
        return json.loads(r.get(key) or "{}")
    except Exception:
        return {}


def summary_cards(reports: list):
    """Six accent-coloured summary cards for the reports dashboard."""
    total = len(reports)
    passed = sum(1 for r in reports if r.get("result") == "Pass")
    failed = sum(1 for r in reports if r.get("result") == "Fail")
    missing = sum(len(_issues(r, "issues_json").get("missing_requirements") or [])
                  for r in reports)
    grammar = sum(len(_issues(r, "issues_json").get("grammar_spelling") or [])
                  for r in reports)
    moa_fail = sum(1 for r in reports if r.get("moa_result") == "Fail")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards.stat_card(c1, total, "Total Courses", "primary")
    cards.stat_card(c2, passed, "Passed", "ok")
    cards.stat_card(c3, failed, "Failed", "err")
    cards.stat_card(c4, missing, "Missing Requirements", "warn")
    cards.stat_card(c5, grammar, "Grammar Issues", "violet")
    cards.stat_card(c6, moa_fail, "MoA Issues", "accent")
    st.write("")


def filter_controls(reports: list) -> list:
    """Search bar + result filter + sort selector. Returns the shaped list."""
    f1, f2, f3 = st.columns([2.4, 1, 1])
    query = f1.text_input("🔎 Search course name", "",
                          placeholder="Start typing a course name…")
    result = f2.selectbox("Filter", ["All results", "Pass only", "Fail only",
                                     "MoA issues"])
    order = f3.selectbox("Sort", ["Newest first", "Oldest first",
                                  "Course name A–Z"])

    out = [r for r in reports
           if query.lower() in (r.get("course_name") or "").lower()]
    if result == "Pass only":
        out = [r for r in out if r.get("result") == "Pass"]
    elif result == "Fail only":
        out = [r for r in out if r.get("result") == "Fail"]
    elif result == "MoA issues":
        out = [r for r in out if r.get("moa_result") == "Fail"]

    if order == "Oldest first":
        out = sorted(out, key=lambda r: r.get("id", 0))
    elif order == "Course name A–Z":
        out = sorted(out, key=lambda r: (r.get("course_name") or "").lower())
    else:  # newest first — all_reports() already returns id DESC
        out = sorted(out, key=lambda r: r.get("id", 0), reverse=True)
    return out
