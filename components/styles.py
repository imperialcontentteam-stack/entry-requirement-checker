"""Global visual system for the Course Content Checker.

The theme uses a professional navy/teal foundation with blue and coral
accents, accessible contrast, responsive spacing, and consistent styling for
Streamlit's native controls. Pure presentation; no business logic lives here.
"""

import streamlit as st

# Brand palette shared by custom components.
PRIMARY = "#0F766E"
PRIMARY_DARK = "#083B4C"
SECONDARY = "#2563EB"
ACCENT = "#F97316"
AQUA = "#14B8A6"
BACKGROUND = "#F3F7FA"
SIDEBAR_BG = "#F8FBFC"
CARD_BG = "#FFFFFF"
BORDER = "#D9E2EC"
SUCCESS = "#16A34A"
WARNING = "#D97706"
ERROR = "#DC2626"
TEXT = "#102A43"
MUTED = "#627D98"

_CSS = f"""
<style>
:root {{
  --cc-primary: {PRIMARY};
  --cc-primary-dark: {PRIMARY_DARK};
  --cc-secondary: {SECONDARY};
  --cc-accent: {ACCENT};
  --cc-aqua: {AQUA};
  --cc-bg: {BACKGROUND};
  --cc-surface: {CARD_BG};
  --cc-border: {BORDER};
  --cc-text: {TEXT};
  --cc-muted: {MUTED};
  --cc-success: {SUCCESS};
  --cc-warning: {WARNING};
  --cc-error: {ERROR};
}}

/* ── Base canvas and typography ─────────────────────────────────── */
html, body, [class*="css"], .stApp {{
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: {TEXT};
}}
.stApp {{
  background:
    radial-gradient(circle at 82% 4%, rgba(37,99,235,.07), transparent 24rem),
    radial-gradient(circle at 18% 95%, rgba(20,184,166,.07), transparent 28rem),
    {BACKGROUND};
}}
h1, h2, h3 {{
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: {TEXT};
  letter-spacing: -.025em;
}}
h2 {{ font-size: 1.45rem !important; margin-top: 1.8rem !important; }}
h3 {{ font-size: 1.10rem !important; }}
p, li, label, .stMarkdown, .stCaption,
div[data-testid="stWidgetLabel"] p {{ color: {TEXT}; }}
.stCaption, div[data-testid="stCaptionContainer"] p, small {{ color: {MUTED} !important; }}
a {{ color: {SECONDARY}; text-decoration-thickness: 1px; text-underline-offset: 3px; }}
a:hover {{ color: {PRIMARY}; }}
.block-container {{
  padding-top: 1.4rem;
  padding-bottom: 4rem;
  max-width: 1280px;
}}

/* ── Streamlit chrome ───────────────────────────────────────────── */
header[data-testid="stHeader"] {{ background: transparent; box-shadow: none; }}
header[data-testid="stHeader"] * {{ color: {MUTED}; }}
#MainMenu, footer {{ visibility: hidden; }}
.stDeployButton, a[data-testid="stAppDeployButton"] {{ display: none; }}
div[data-testid="stDecoration"] {{ display: none; }}

/* ── Page animation ─────────────────────────────────────────────── */
@keyframes ccFadeUp {{
  from {{ opacity: 0; transform: translateY(7px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes ccFloat {{
  0%, 100% {{ transform: translate3d(0,0,0); }}
  50% {{ transform: translate3d(0,-7px,0); }}
}}
.app-hero {{ animation: ccFadeUp .18s ease-out; }}

/* ── Hero header ────────────────────────────────────────────────── */
.app-hero {{
  position: relative;
  overflow: hidden;
  min-height: 176px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  background: linear-gradient(125deg, {PRIMARY_DARK} 0%, {PRIMARY} 48%, {SECONDARY} 105%);
  border: 1px solid rgba(255,255,255,.14);
  border-radius: 24px;
  padding: 30px 34px;
  margin: 2px 0 24px;
  box-shadow: 0 18px 50px rgba(8,59,76,.20);
}}
.app-hero::before {{
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(90deg, transparent, #000 45%, #000);
}}
.app-hero::after {{
  content: "";
  position: absolute;
  width: 320px;
  height: 320px;
  right: -110px;
  top: -125px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,.24), rgba(255,255,255,.03) 58%, transparent 59%);
}}
.hero-copy {{ position: relative; z-index: 2; max-width: 820px; }}
.app-hero .eyebrow {{
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 11px;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,.28);
  border-radius: 999px;
  background: rgba(255,255,255,.11);
  color: #E6FFFB !important;
  font-size: .72rem;
  line-height: 1;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  backdrop-filter: blur(8px);
}}
.app-hero .eyebrow-dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #5EEAD4;
  box-shadow: 0 0 0 4px rgba(94,234,212,.16);
}}
.app-hero h1 {{
  margin: 0;
  max-width: 820px;
  color: #FFFFFF !important;
  font-size: clamp(1.65rem, 2.5vw, 2.35rem);
  line-height: 1.14;
  font-weight: 800;
  letter-spacing: -.04em;
}}
.app-hero p {{
  margin: .65rem 0 0;
  max-width: 760px;
  color: #D8F3F1 !important;
  font-size: .98rem;
  line-height: 1.55;
}}
.hero-orbit {{
  position: relative;
  z-index: 2;
  flex: 0 0 128px;
  height: 112px;
  display: grid;
  place-items: center;
  animation: ccFloat 5s ease-in-out infinite;
}}
.hero-orbit .orb-main {{
  width: 74px;
  height: 74px;
  display: grid;
  place-items: center;
  border-radius: 24px;
  background: rgba(255,255,255,.16);
  border: 1px solid rgba(255,255,255,.32);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.28), 0 16px 28px rgba(0,0,0,.16);
  backdrop-filter: blur(12px);
  color: #FFFFFF;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 1.55rem;
  font-weight: 800;
}}
.hero-orbit .orb-a, .hero-orbit .orb-b {{
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,.4);
}}
.hero-orbit .orb-a {{ width: 18px; height: 18px; right: 6px; top: 4px; background: #FDBA74; }}
.hero-orbit .orb-b {{ width: 11px; height: 11px; left: 3px; bottom: 8px; background: #5EEAD4; }}

/* ── Section headings and dividers ─────────────────────────────── */
div[data-testid="stHeadingWithActionElements"] h1,
div[data-testid="stHeadingWithActionElements"] h2,
div[data-testid="stHeadingWithActionElements"] h3 {{ position: relative; }}
hr {{ border-color: {BORDER} !important; margin: 1.7rem 0 !important; }}

/* ── Metric/stat cards ──────────────────────────────────────────── */
.stat-card {{
  position: relative;
  min-height: 116px;
  overflow: hidden;
  border-radius: 18px;
  padding: 18px 18px 16px;
  border: 1px solid {BORDER};
  background: linear-gradient(155deg, #FFFFFF 0%, #FBFDFE 100%);
  box-shadow: 0 7px 22px rgba(16,42,67,.065);
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}}
.stat-card::after {{
  content: "";
  position: absolute;
  width: 88px;
  height: 88px;
  right: -28px;
  bottom: -34px;
  border-radius: 50%;
  background: var(--card-tint, rgba(15,118,110,.10));
}}
.stat-card:hover {{
  transform: translateY(-3px);
  border-color: rgba(15,118,110,.30);
  box-shadow: 0 14px 32px rgba(8,59,76,.12);
}}
.stat-card .card-icon {{
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  margin-bottom: 9px;
  border-radius: 9px;
  background: var(--card-tint, rgba(15,118,110,.12));
  color: var(--card-color, {PRIMARY});
  font-size: .78rem;
  font-weight: 800;
}}
.stat-card .num {{
  position: relative;
  z-index: 1;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: clamp(1.35rem, 2vw, 1.85rem);
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -.04em;
  color: {TEXT};
  overflow-wrap: anywhere;
}}
.stat-card .lbl {{
  position: relative;
  z-index: 1;
  margin-top: 5px;
  color: {MUTED};
  font-size: .69rem;
  line-height: 1.25;
  font-weight: 700;
  letter-spacing: .075em;
  text-transform: uppercase;
}}
.stat-card.primary, .stat-card.info {{ --card-color:{PRIMARY}; --card-tint:rgba(15,118,110,.12); }}
.stat-card.violet {{ --card-color:#7C3AED; --card-tint:rgba(124,58,237,.11); }}
.stat-card.accent {{ --card-color:{ACCENT}; --card-tint:rgba(249,115,22,.12); }}
.stat-card.ok {{ --card-color:{SUCCESS}; --card-tint:rgba(22,163,74,.11); }}
.stat-card.err {{ --card-color:{ERROR}; --card-tint:rgba(220,38,38,.10); }}
.stat-card.warn {{ --card-color:{WARNING}; --card-tint:rgba(217,119,6,.12); }}

/* ── Badges ─────────────────────────────────────────────────────── */
.badge {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-weight: 700;
  font-size: .76rem;
  line-height: 1;
}}
.badge::before {{ content:""; width:7px; height:7px; border-radius:50%; background:currentColor; }}
.badge.pass {{ color:#15803D; background:#F0FDF4; border-color:#BBF7D0; }}
.badge.fail {{ color:#B91C1C; background:#FEF2F2; border-color:#FECACA; }}
.badge.warn {{ color:#B45309; background:#FFFBEB; border-color:#FDE68A; }}
.badge.neutral {{ color:#1D4ED8; background:#EFF6FF; border-color:#BFDBFE; }}

/* ── Buttons ────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {{
  min-height: 42px;
  border-radius: 11px;
  border: 1px solid {BORDER};
  background: #FFFFFF;
  color: {TEXT};
  font-weight: 700;
  letter-spacing: -.01em;
  box-shadow: 0 2px 6px rgba(16,42,67,.04);
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease, background .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  transform: translateY(-1px);
  border-color: rgba(15,118,110,.48);
  color: {PRIMARY};
  background: #F6FFFD;
  box-shadow: 0 8px 18px rgba(8,59,76,.12);
}}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
  outline: 3px solid rgba(37,99,235,.22) !important;
  outline-offset: 2px;
}}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  border: 0;
  color: #FFFFFF;
  background: linear-gradient(120deg, {PRIMARY_DARK}, {PRIMARY} 58%, {AQUA});
  box-shadow: 0 9px 20px rgba(15,118,110,.22);
}}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {{
  color: #FFFFFF;
  border: 0;
  background: linear-gradient(120deg, #062F3D, #0D857B 58%, #13A89A);
  box-shadow: 0 12px 24px rgba(15,118,110,.28);
}}
.stButton > button:disabled {{ opacity:.55; box-shadow:none; transform:none; }}

/* ── Sidebar ────────────────────────────────────────────────────── */
div[data-testid="stSidebar"] {{
  background:
    linear-gradient(180deg, rgba(15,118,110,.055), transparent 185px),
    {SIDEBAR_BG};
  border-right: 1px solid {BORDER};
  box-shadow: 10px 0 32px rgba(16,42,67,.035);
}}
div[data-testid="stSidebar"] .block-container {{ padding: 1.15rem 1rem 1.2rem; }}
div[data-testid="stSidebar"] p,
div[data-testid="stSidebar"] label,
div[data-testid="stSidebar"] span {{ color: {TEXT}; }}
.sb-logo {{
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 5px 3px 17px;
  border-bottom: 1px solid {BORDER};
  margin-bottom: 14px;
}}
.sb-logo .mark {{
  position: relative;
  flex: 0 0 43px;
  width: 43px;
  height: 43px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #FFFFFF !important;
  background: linear-gradient(145deg, {PRIMARY_DARK}, {PRIMARY} 60%, {AQUA});
  box-shadow: 0 9px 20px rgba(15,118,110,.23);
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: .92rem;
  font-weight: 800;
}}
.sb-logo .mark::after {{
  content:"";
  position:absolute;
  width:8px; height:8px;
  right:-2px; top:-2px;
  border-radius:50%;
  border:2px solid {SIDEBAR_BG};
  background:{ACCENT};
}}
.sb-logo .name {{
  color: {TEXT} !important;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: .96rem;
  line-height: 1.18;
  font-weight: 800;
  letter-spacing: -.025em;
}}
.sb-logo .sub {{ margin-top:3px; color:{MUTED} !important; font-size:.67rem; line-height:1.25; }}
.sb-section-label {{
  padding: 2px 8px 7px;
  color: {MUTED};
  font-size: .65rem;
  font-weight: 800;
  letter-spacing: .11em;
  text-transform: uppercase;
}}
div[data-testid="stSidebar"] div[role="radiogroup"] {{ gap: 4px; }}
div[data-testid="stSidebar"] div[role="radiogroup"] > label {{
  width: 100%;
  min-height: 43px;
  margin: 0;
  padding: 9px 11px;
  border: 1px solid transparent;
  border-radius: 11px;
  transition: background .15s ease, border-color .15s ease, transform .15s ease;
}}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
  transform: translateX(2px);
  background: #EEF8F6;
  border-color: rgba(15,118,110,.11);
}}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
  color: {PRIMARY_DARK};
  background: linear-gradient(100deg, rgba(15,118,110,.13), rgba(37,99,235,.07));
  border-color: rgba(15,118,110,.25);
  box-shadow: inset 3px 0 0 {PRIMARY};
  font-weight: 700;
}}
div[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{ display:none; }}
.sb-status {{
  display:flex;
  align-items:center;
  gap:9px;
  margin:17px 1px 0;
  padding:10px 11px;
  border-radius:12px;
  border:1px solid;
  font-size:.72rem;
  line-height:1.35;
  font-weight:600;
}}
.sb-status .dot {{ width:8px; height:8px; flex:0 0 8px; border-radius:50%; }}
.sb-status.ok {{ color:#166534; background:#F0FDF4; border-color:#BBF7D0; }}
.sb-status.ok .dot {{ background:#22C55E; box-shadow:0 0 0 4px rgba(34,197,94,.12); }}
.sb-status.err {{ color:#991B1B; background:#FFF7F7; border-color:#FECACA; }}
.sb-status.err .dot {{ background:#EF4444; box-shadow:0 0 0 4px rgba(239,68,68,.11); }}
.sb-footer {{
  margin-top: 16px;
  padding: 13px 3px 0;
  border-top: 1px solid {BORDER};
  color: {MUTED};
  font-size: .68rem;
  line-height: 1.55;
}}
.sb-footer b {{ color: {PRIMARY_DARK}; }}
.version-pill {{
  display:inline-block;
  margin-bottom:5px;
  padding:2px 7px;
  border-radius:999px;
  color:{PRIMARY_DARK};
  background:#E6F6F3;
  font-weight:800;
}}

/* ── Form controls ──────────────────────────────────────────────── */
div[data-testid="stWidgetLabel"] p {{ font-weight: 700; font-size: .86rem; }}
.stTextInput input, .stTextArea textarea,
.stNumberInput input, .stDateInput input,
div[data-baseweb="select"] > div {{
  border-radius: 11px !important;
  border-color: {BORDER} !important;
  background: #FFFFFF !important;
  color: {TEXT} !important;
  box-shadow: 0 1px 3px rgba(16,42,67,.03);
}}
.stTextInput input:hover, .stTextArea textarea:hover,
div[data-baseweb="select"] > div:hover {{ border-color: rgba(15,118,110,.45) !important; }}
.stTextInput input:focus, .stTextArea textarea:focus,
.stNumberInput input:focus {{
  border-color: {PRIMARY} !important;
  box-shadow: 0 0 0 3px rgba(15,118,110,.13) !important;
}}
div[data-baseweb="popover"] {{ border-radius:12px; overflow:hidden; }}

/* Radio pills outside the sidebar */
div[data-testid="stMainBlockContainer"] div[role="radiogroup"] {{ gap:7px; }}
div[data-testid="stMainBlockContainer"] div[role="radiogroup"] > label {{
  padding:7px 11px;
  border:1px solid {BORDER};
  border-radius:999px;
  background:#FFFFFF;
}}
div[data-testid="stMainBlockContainer"] div[role="radiogroup"] > label:has(input:checked) {{
  border-color:rgba(15,118,110,.36);
  background:#EAF8F5;
  color:{PRIMARY_DARK};
}}

/* ── File uploader ──────────────────────────────────────────────── */
div[data-testid="stFileUploader"] section {{
  min-height: 140px;
  padding: 24px;
  border: 1.5px dashed rgba(15,118,110,.55);
  border-radius: 18px;
  background:
    radial-gradient(circle at 92% 10%, rgba(37,99,235,.08), transparent 9rem),
    linear-gradient(145deg, #F7FFFD, #F7FAFF);
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}}
div[data-testid="stFileUploader"] section:hover {{
  transform: translateY(-1px);
  border-color: {PRIMARY};
  box-shadow: 0 10px 24px rgba(8,59,76,.08);
}}
div[data-testid="stFileUploader"] section span,
div[data-testid="stFileUploader"] section div {{ color:{TEXT} !important; }}
div[data-testid="stFileUploader"] section small {{ color:{MUTED} !important; }}
div[data-testid="stFileUploader"] section svg {{ fill:{PRIMARY}; color:{PRIMARY}; }}
div[data-testid="stFileUploader"] section button {{
  border:0 !important;
  border-radius:10px !important;
  color:#FFFFFF !important;
  background:linear-gradient(120deg,{PRIMARY_DARK},{PRIMARY}) !important;
  font-weight:700 !important;
}}
div[data-testid="stFileUploaderFile"] {{ color:{TEXT}; }}

/* ── Tabs ───────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  gap: 6px;
  padding: 5px;
  border-radius: 13px;
  background: #EAF0F4;
}}
.stTabs [data-baseweb="tab"] {{
  min-height: 39px;
  padding: 7px 14px;
  border-radius: 9px;
  color: {MUTED};
  font-weight: 700;
}}
.stTabs [data-baseweb="tab"]:hover {{ color:{PRIMARY}; background:rgba(255,255,255,.60); }}
.stTabs [aria-selected="true"] {{ color:{PRIMARY_DARK} !important; background:#FFFFFF !important; box-shadow:0 3px 10px rgba(16,42,67,.09); }}
.stTabs [data-baseweb="tab-highlight"] {{ display:none; }}
.stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* ── Expanders, containers, dialogs ────────────────────────────── */
div[data-testid="stExpander"] {{
  overflow: hidden;
  border: 1px solid {BORDER};
  border-radius: 15px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 5px 16px rgba(16,42,67,.045);
}}
div[data-testid="stExpander"] summary {{ padding-top:3px; padding-bottom:3px; }}
div[data-testid="stExpander"] summary:hover {{ background:#F7FAFC; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: {BORDER} !important;
  border-radius: 16px !important;
  box-shadow: 0 5px 16px rgba(16,42,67,.04);
}}

/* ── Tables and dataframes ──────────────────────────────────────── */
div[data-testid="stDataFrame"] {{
  overflow: hidden;
  border: 1px solid {BORDER};
  border-radius: 15px;
  background:#FFFFFF;
  box-shadow: 0 7px 22px rgba(16,42,67,.055);
}}
div[data-testid="stDataFrame"] [role="columnheader"] {{
  background:#EEF5F7 !important;
  color:{PRIMARY_DARK} !important;
  font-weight:800 !important;
}}

/* ── Progress and spinner ───────────────────────────────────────── */
.stProgress > div > div > div > div {{
  border-radius:999px;
  background: linear-gradient(90deg, {PRIMARY}, {AQUA}, {SECONDARY});
}}
.stProgress > div > div {{ background:#DDE8EC; border-radius:999px; }}
div[data-testid="stSpinner"] {{ color:{PRIMARY}; }}
.progress-status {{
  margin-top:8px;
  padding:10px 13px;
  border:1px solid {BORDER};
  border-radius:11px;
  background:#FFFFFF;
  color:{MUTED};
  font-size:.82rem;
}}
.progress-status b {{ color:{TEXT}; }}

/* ── Alerts ─────────────────────────────────────────────────────── */
div[data-testid="stAlert"] {{
  border-radius: 13px;
  border-width: 1px;
  box-shadow: 0 4px 14px rgba(16,42,67,.045);
}}
div[data-testid="stAlert"] p {{ color:inherit; }}

/* ── Code and text areas ───────────────────────────────────────── */
.stTextArea textarea, .stTextInput input {{ color:{TEXT}; background:#FFFFFF; }}
code {{ border-radius:6px; color:{PRIMARY_DARK}; background:#EAF5F3; }}

/* ── Responsive refinements ────────────────────────────────────── */
@media (max-width: 900px) {{
  .block-container {{ padding-left:1rem; padding-right:1rem; padding-top:1rem; }}
  .app-hero {{ min-height:auto; padding:24px; border-radius:20px; }}
  .hero-orbit {{ display:none; }}
  .app-hero h1 {{ font-size:1.7rem; }}
  .stat-card {{ min-height:104px; padding:15px; }}
}}
@media (max-width: 640px) {{
  .app-hero {{ padding:21px 19px; margin-bottom:18px; }}
  .app-hero p {{ font-size:.9rem; }}
  .app-hero .eyebrow {{ font-size:.65rem; }}
  h2 {{ font-size:1.28rem !important; }}
  .stButton > button, .stDownloadButton > button {{ width:100%; }}
}}

/* Respect reduced-motion user preferences. */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; }}
}}
</style>
"""


def inject():
    """Inject the global CSS once per Streamlit rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)
