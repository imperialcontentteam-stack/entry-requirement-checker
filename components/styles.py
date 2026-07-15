"""Global theme for the app — modern purple palette, Inter/Poppins fonts,
rounded cards, soft shadows and light animations. Injected once per run
with st.markdown(); pure presentation, no business logic."""

import streamlit as st

# ── Palette ──────────────────────────────────────────────────────────
PRIMARY = "#6C63FF"
SECONDARY = "#8B5CF6"
ACCENT = "#A855F7"
BACKGROUND = "#F8F7FF"
SIDEBAR_BG = "#FFFFFF"
CARD_BG = "#FFFFFF"
BORDER = "#E5E7EB"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
ERROR = "#EF4444"
TEXT = "#1F2140"
MUTED = "#6B7280"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');

/* ── Base ─────────────────────────────────────── */
html, body, [class*="css"], .stApp {{ font-family:'Inter',sans-serif; color:{TEXT}; }}
.stApp {{ background:{BACKGROUND}; }}
h1,h2,h3 {{ font-family:'Poppins','Inter',sans-serif; letter-spacing:.2px; color:{TEXT}; }}
p, li, label, .stMarkdown, .stCaption, div[data-testid="stWidgetLabel"] p {{ color:{TEXT}; }}
.stCaption, div[data-testid="stCaptionContainer"] p, small {{ color:{MUTED} !important; }}
.block-container {{ padding-top:1.2rem; padding-bottom:3rem; max-width:1200px; }}

/* ── Hide default Streamlit chrome (real-website look) ── */
header[data-testid="stHeader"] {{ background:transparent; box-shadow:none; }}
header[data-testid="stHeader"] * {{ color:{MUTED}; }}
#MainMenu, footer {{ visibility:hidden; }}
/* Keep the toolbar container: Streamlit puts the sidebar reopen button inside it. */
.stDeployButton, a[data-testid="stAppDeployButton"] {{ display:none; }}
div[data-testid="stDecoration"] {{ display:none; }}

/* ── Fade-in animation for main content ──────── */
@keyframes fadeUp {{ from {{opacity:0; transform:translateY(8px);}} to {{opacity:1; transform:none;}} }}
.block-container > div {{ animation: fadeUp .35s ease-out; }}

/* ── Hero / page header ───────────────────────── */
.app-hero {{
  background: linear-gradient(120deg, {PRIMARY} 0%, {SECONDARY} 55%, {ACCENT} 100%);
  border-radius:20px; padding:26px 32px; margin-bottom:20px;
  box-shadow:0 10px 30px rgba(108,99,255,.28); position:relative; overflow:hidden;
}}
.app-hero:before {{
  content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px;
  background: radial-gradient(circle, rgba(255,255,255,.28), transparent 70%);
}}
.app-hero h1 {{ color:#fff; margin:0; font-size:1.7rem; font-weight:800; }}
.app-hero p  {{ color:#EDEAFF; margin:.4rem 0 0; font-size:.95rem; }}
.app-hero .chip {{
  display:inline-block; background:rgba(255,255,255,.18); color:#fff;
  border:1px solid rgba(255,255,255,.35); border-radius:999px;
  padding:3px 12px; font-size:.75rem; font-weight:600; margin-bottom:10px;
}}

/* ── Cards & stat cards ───────────────────────── */
.stat-card {{
  border-radius:16px; padding:16px 18px; border:1px solid {BORDER};
  background:{CARD_BG}; box-shadow:0 3px 14px rgba(31,33,64,.06);
  transition: transform .18s ease, box-shadow .18s ease;
}}
.stat-card:hover {{ transform:translateY(-3px); box-shadow:0 10px 24px rgba(108,99,255,.16); }}
.stat-card .num {{ font-family:'Poppins',sans-serif; font-size:1.8rem; font-weight:800; line-height:1.1; color:{TEXT}; }}
.stat-card .lbl {{ font-size:.74rem; text-transform:uppercase; letter-spacing:.09em; color:{MUTED}; font-weight:600; margin-top:2px; }}
.stat-card.primary {{ border-top:4px solid {PRIMARY}; }}
.stat-card.violet  {{ border-top:4px solid {SECONDARY}; }}
.stat-card.accent  {{ border-top:4px solid {ACCENT}; }}
.stat-card.ok      {{ border-top:4px solid {SUCCESS}; }}
.stat-card.err     {{ border-top:4px solid {ERROR}; }}
.stat-card.warn    {{ border-top:4px solid {WARNING}; }}
.stat-card.info    {{ border-top:4px solid {PRIMARY}; }}

/* ── Status badges ────────────────────────────── */
.badge {{
  display:inline-block; padding:3px 14px; border-radius:999px;
  font-weight:700; font-size:.82rem; color:#fff;
}}
.badge.pass {{ background:{SUCCESS}; }}
.badge.fail {{ background:{ERROR}; }}
.badge.warn {{ background:{WARNING}; }}
.badge.neutral {{ background:{SECONDARY}; }}

/* ── Buttons ──────────────────────────────────── */
.stButton>button, .stDownloadButton>button {{
  border-radius:12px; font-weight:600; border:1px solid {BORDER};
  background:{CARD_BG}; color:{TEXT};
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}}
.stButton>button:hover, .stDownloadButton>button:hover {{
  transform:translateY(-1px); box-shadow:0 6px 16px rgba(108,99,255,.22);
  border-color:{PRIMARY}; color:{PRIMARY};
}}
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {{
  background:linear-gradient(120deg,{PRIMARY},{ACCENT}); border:none; color:#fff;
}}
.stButton>button[kind="primary"]:hover {{ filter:brightness(1.06); color:#fff; }}

/* ── Sidebar ──────────────────────────────────── */
div[data-testid="stSidebar"] {{ background:{SIDEBAR_BG}; border-right:1px solid {BORDER}; }}
div[data-testid="stSidebar"] .block-container {{ padding-top:1rem; }}
div[data-testid="stSidebar"] p, div[data-testid="stSidebar"] label,
div[data-testid="stSidebar"] span {{ color:{TEXT}; }}
.sb-logo {{
  display:flex; align-items:center; gap:10px; padding:6px 2px 14px;
  border-bottom:1px solid {BORDER}; margin-bottom:12px;
}}
.sb-logo .mark {{
  width:40px; height:40px; border-radius:12px; display:flex; align-items:center;
  justify-content:center; font-size:1.25rem; color:#fff;
  background:linear-gradient(135deg,{PRIMARY},{ACCENT});
  box-shadow:0 6px 14px rgba(108,99,255,.35);
}}
.sb-logo .name {{ font-family:'Poppins',sans-serif; font-weight:700; font-size:1rem; line-height:1.2; color:{TEXT}; }}
.sb-logo .sub  {{ font-size:.72rem; color:{MUTED}; }}
.sb-footer {{
  border-top:1px solid {BORDER}; margin-top:14px; padding-top:10px;
  font-size:.74rem; color:{MUTED};
}}
/* sidebar radio → nav menu look */
div[data-testid="stSidebar"] div[role="radiogroup"] > label {{
  border-radius:12px; padding:9px 12px; margin:2px 0; width:100%;
  transition: background .15s ease;
}}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{ background:{BACKGROUND}; }}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
  background:linear-gradient(120deg,rgba(108,99,255,.14),rgba(168,85,247,.14));
  border:1px solid rgba(108,99,255,.35); font-weight:600;
}}

/* ── Tabs ─────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{
  font-weight:600; border-radius:10px 10px 0 0; padding:8px 16px;
}}
.stTabs [aria-selected="true"] {{ color:{PRIMARY}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:{PRIMARY}; }}

/* ── Inputs, selects, uploader, expanders ─────── */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
  border-radius:12px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color:{PRIMARY} !important; box-shadow:0 0 0 2px rgba(108,99,255,.25) !important;
}}
div[data-testid="stFileUploader"] section {{
  border:2px dashed {SECONDARY}; border-radius:16px; background:#FBFAFF;
  padding:22px; transition: border-color .15s ease, background .15s ease;
}}
div[data-testid="stFileUploader"] section:hover {{ border-color:{PRIMARY}; background:#F4F1FF; }}
/* explicit colours so the drop-zone text is always readable */
div[data-testid="stFileUploader"] section span,
div[data-testid="stFileUploader"] section div {{ color:{TEXT} !important; }}
div[data-testid="stFileUploader"] section small {{ color:{MUTED} !important; }}
div[data-testid="stFileUploader"] section svg {{ fill:{PRIMARY}; color:{PRIMARY}; }}
div[data-testid="stFileUploader"] section button {{
  background:linear-gradient(120deg,{PRIMARY},{ACCENT}) !important;
  color:#fff !important; border:none !important; border-radius:10px !important;
  font-weight:600 !important;
}}
div[data-testid="stFileUploaderFile"] {{ color:{TEXT}; }}
div[data-testid="stExpander"] {{
  border:1px solid {BORDER}; border-radius:14px; background:{CARD_BG};
  box-shadow:0 2px 10px rgba(31,33,64,.05); overflow:hidden;
}}

/* ── Tables / dataframes ──────────────────────── */
div[data-testid="stDataFrame"] {{
  border:1px solid {BORDER}; border-radius:14px; overflow:hidden;
  box-shadow:0 2px 10px rgba(31,33,64,.05);
}}

/* ── Progress bar ─────────────────────────────── */
.stProgress > div > div > div > div {{
  background:linear-gradient(90deg,{PRIMARY},{ACCENT});
}}

/* ── Alerts polish ────────────────────────────── */
div[data-testid="stAlert"] {{ border-radius:12px; }}
div[data-testid="stAlert"] p {{ color:inherit; }}

/* hero text must stay white whatever the base theme */
.app-hero h1, .app-hero p, .app-hero .chip {{ color:#fff !important; }}
.app-hero p {{ color:#EDEAFF !important; }}

/* text areas / code readable on light background */
.stTextArea textarea {{ color:{TEXT}; background:#FFFFFF; }}
.stTextInput input {{ color:{TEXT}; background:#FFFFFF; }}
</style>
"""


def inject():
    """Inject the global CSS once per rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)
