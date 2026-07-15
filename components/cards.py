"""Reusable metric cards and status badges."""

import html

import streamlit as st

_KIND_ICONS = {
    "primary": "◆",
    "info": "◆",
    "violet": "✦",
    "accent": "●",
    "ok": "✓",
    "err": "!",
    "warn": "△",
}


def stat_card(col, value, label, kind: str = "primary"):
    """Render a compact metric card with a semantic accent."""
    safe_value = html.escape(str(value))
    safe_label = html.escape(str(label))
    icon = _KIND_ICONS.get(kind, "◆")
    col.markdown(
        f'<div class="stat-card {kind}">'
        f'<div class="card-icon">{icon}</div>'
        f'<div class="num">{safe_value}</div>'
        f'<div class="lbl">{safe_label}</div></div>',
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = None) -> str:
    """Return an HTML status badge; Pass and Fail select their own colour."""
    safe_text = html.escape(str(text))
    if kind is None:
        kind = {"pass": "pass", "fail": "fail"}.get(str(text).lower(), "neutral")
    return f'<span class="badge {kind}">{safe_text}</span>'
