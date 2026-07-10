"""Upload-area helpers: supported-file info box and post-upload details."""

import streamlit as st


def info(kinds: str, note: str = ""):
    st.caption(f"**Supported:** {kinds}" + (f" · {note}" if note else ""))


def file_details(file):
    """Show name/size/type after a successful upload."""
    if file is None:
        return
    size_kb = getattr(file, "size", 0) / 1024
    size = f"{size_kb/1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.0f} KB"
    st.markdown(
        f'<div class="stat-card violet" style="padding:10px 16px">'
        f'📎 <b>{file.name}</b> &nbsp;·&nbsp; {size} &nbsp;·&nbsp; ready to import'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")
