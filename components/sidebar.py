"""Modern sidebar: logo, app name, navigation menu, AI-connection status,
version number and footer. Returns the selected page label."""

import streamlit as st

PAGES = ["📥 Upload & Specs", "▶️ Run Check", "📄 Reports",
         "✍️ Content Quality", "🗂️ Manage Data"]


def render(version: str, api_key_present: bool) -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="sb-logo">
              <div class="mark">✓</div>
              <div>
                <div class="name">Course Content Checker</div>
                <div class="sub">Entry Requirements · MoA · Quality</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        page = st.radio("Navigation", PAGES, label_visibility="collapsed")

        st.markdown("")
        if api_key_present:
            st.success("🔑 OpenRouter connected (US hosts)", icon="✅")
        else:
            st.error("Add `OPENROUTER_API_KEY` to Streamlit Secrets", icon="🔑")

        st.markdown(
            f"""
            <div class="sb-footer">
              <b>v{version}</b> · Purple edition<br>
              Compares course pages against qualification
              specifications and proofreads content.
            </div>
            """,
            unsafe_allow_html=True,
        )
    return page
