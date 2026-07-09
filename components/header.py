"""Gradient hero header shown at the top of every page."""

import streamlit as st


def page_header(title: str, subtitle: str = "", chip: str = "AI-powered checks"):
    st.markdown(
        f"""
        <div class="app-hero">
          <span class="chip">✦ {chip}</span>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
