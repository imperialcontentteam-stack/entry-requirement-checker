"""Branded page hero shown at the top of each application page."""

import html

import streamlit as st


def page_header(title: str, subtitle: str = "", chip: str = "AI-powered workspace"):
    """Render a responsive hero with safely escaped user-facing copy."""
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_chip = html.escape(chip)
    st.markdown(
        f"""
        <section class="app-hero" aria-label="Page introduction">
          <div class="hero-copy">
            <div class="eyebrow"><span class="eyebrow-dot"></span>{safe_chip}</div>
            <h1>{safe_title}</h1>
            <p>{safe_subtitle}</p>
          </div>
          <div class="hero-orbit" aria-hidden="true">
            <span class="orb-a"></span>
            <div class="orb-main">CC</div>
            <span class="orb-b"></span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
