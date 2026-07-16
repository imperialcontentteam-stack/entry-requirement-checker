"""Branded sidebar with navigation, connection state and version details."""

import streamlit as st

PAGES = ["📥 Upload & Specs", "▶️ Run Check", "📄 Reports",
         "✍️ Content Quality", "🧭 Course Overview Quality",
         "🗂️ Manage Data"]


def render(version: str, api_key_present: bool) -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="sb-logo">
              <div class="mark">CC</div>
              <div>
                <div class="name">Course Content<br>Checker</div>
                <div class="sub">Validation · compliance · quality</div>
              </div>
            </div>
            <div class="sb-section-label">Workspace</div>
            """,
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigation",
            PAGES,
            key="main_navigation",
            label_visibility="collapsed",
        )

        if api_key_present:
            status_class = "ok"
            status_text = "AI service connected"
        else:
            status_class = "err"
            status_text = "OpenRouter API key required"
        st.markdown(
            f'<div class="sb-status {status_class}"><span class="dot"></span>'
            f'<span>{status_text}</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="sb-footer">
              <span class="version-pill">Version {version}</span><br>
              Compare course pages with qualification specifications, create
              reports, proofread content, and evaluate course-overview quality from one workspace.
            </div>
            """,
            unsafe_allow_html=True,
        )
    return page
