"""Reusable stat cards and status badges (pure presentation)."""

import streamlit as st


def stat_card(col, value, label, kind: str = "primary"):
    """Rounded stat card with a coloured top accent.
    kind: primary | violet | accent | ok | err | warn | info"""
    col.markdown(
        f'<div class="stat-card {kind}"><div class="num">{value}</div>'
        f'<div class="lbl">{label}</div></div>',
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = None) -> str:
    """HTML status badge. kind defaults from text: Pass→green, Fail→red."""
    if kind is None:
        kind = {"pass": "pass", "fail": "fail"}.get(str(text).lower(), "neutral")
    return f'<span class="badge {kind}">{text}</span>'
