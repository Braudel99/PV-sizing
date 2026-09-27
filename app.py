# app.py — PV Sizing v1.5
import streamlit as st
import hashlib, json
from datetime import datetime
from parametres import init_session_state, get_params, render_parametres
from dashboard  import render_dashboard
from engines    import run_sizing
from reports    import generate_technical_pdf, generate_client_pdf

st.set_page_config(
    page_title="PV Sizing — Dimensionnement solaire",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session_state()

if "dark_mode"        not in st.session_state: st.session_state.dark_mode        = True
if "show_results"     not in st.session_state: st.session_state.show_results     = False
if "last_params_hash" not in st.session_state: st.session_state.last_params_hash = ""

# ── Palettes ──────────────────────────────────────────────────────────────────
if st.session_state.dark_mode:
    BG        = "#181C24"
    CARD      = "#1F2433"
    TEXT      = "#CDD1DC"
    TEXT2     = "#7A8299"
    BORDER    = "#2C3245"
    INPUT_BG  = "#161A26"
    ACCENT    = "#7B9ED4"
    # Bouton simulation — bleu roi vif, très lisible sur fond sombre
    SIM_BG    = "#1A56B0"
    SIM_HOVER = "#1D64CC"
    SIM_TXT   = "#FFFFFF"
    SIM_GLOW  = "rgba(26,86,176,0.55)"
    THM_BG    = "#2C3245"
    THM_TXT   = "#CDD1DC"
    METRIC_BG = "rgba(255,255,255,0.03)"
    METRIC_BD = "rgba(255,255,255,0.07)"
    HR        = "rgba(255,255,255,0.06)"
    SHADOW    = "0 2px 14px rgba(0,0,0,0.4)"
    ICON_MODE = "☀️"
    LBL_MODE  = "Mode clair"
else:
    BG        = "#ECEEF4"
    CARD      = "#F6F7FA"
    TEXT      = "#2A2F3E"
    TEXT2     = "#6B7186"
    BORDER    = "#D4D7E3"
    INPUT_BG  = "#FFFFFF"
    ACCENT    = "#2B5BAA"
    # Bouton simulation — bleu marine, lisible sur fond clair
    SIM_BG    = "#1A4A96"
    SIM_HOVER = "#1D57B2"
    SIM_TXT   = "#FFFFFF"
    SIM_GLOW  = "rgba(26,74,150,0.35)"
    THM_BG    = "#DDE0EA"
    THM_TXT   = "#2A2F3E"
    METRIC_BG = "rgba(0,0,0,0.025)"
    METRIC_BD = "rgba(0,0,0,0.06)"
    HR        = "rgba(0,0,0,0.07)"
    SHADOW    = "0 2px 12px rgba(0,0,0,0.07)"
    ICON_MODE = "🌙"
    LBL_MODE  = "Mode sombre"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT} !important;
}}
.block-container {{
    max-width: 900px !important;
    margin: 0 auto !important;
    padding-top: 1.6rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* ── Bandeau Streamlit par défaut ── */
header[data-testid="stHeader"] {{
    height: 2.2rem !important;
    background: transparent !important;
}}
div[data-testid="stDecoration"] {{ display: none !important; }}

/* Typographie */
h1, h2, h3 {{ font-family:'IBM Plex Mono',monospace !important; color:{TEXT} !important; }}
p, .stMarkdown p, label, .stCaption, small {{ color:{TEXT2} !important; font-size:13px; }}
hr {{ border-color:{HR} !important; margin:16px 0 !important; }}

/* ── Métriques ── */
[data-testid="metric-container"] {{
    background:{METRIC_BG} !important;
    border:1px solid {METRIC_BD} !important;
    border-radius:12px !important;
    padding:14px 16px !important;
    transition: transform 0.15s, box-shadow 0.15s;
}}
[data-testid="metric-container"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 18px rgba(0,0,0,0.15);
}}
[data-testid="stMetricValue"] {{
    color:{ACCENT} !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-weight:700 !important;
    font-size:22px !important;
}}
[data-testid="stMetricLabel"] {{ color:{TEXT2} !important; font-size:11px !important; font-weight:500; letter-spacing:0.04em; }}
[data-testid="stMetricDelta"] {{ font-size:11px !important; }}

/* ── Expanders ── */
[data-testid="stExpander"] {{
    background:{CARD} !important;
    border:1px solid {BORDER} !important;
    border-radius:12px !important;
    box-shadow:{SHADOW} !important;
    margin-bottom:14px !important;
    overflow:hidden;
}}
details > summary {{
    padding: 14px 18px !important;
    border-radius: 12px !important;
}}
details summary span {{
    font-weight:600 !important;
    color:{TEXT} !important;
    font-size:14px !important;
}}

/* ── Inputs & selects ── */
input[type="text"], input[type="number"], textarea {{
    background-color:{INPUT_BG} !important;
    color:{TEXT} !important;
    border:1px solid {BORDER} !important;
    border-radius:8px !important;
    font-size:13px !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}}
input[type="text"]:focus, input[type="number"]:focus {{
    border-color:{ACCENT} !important;
    box-shadow: 0 0 0 3px {METRIC_BD} !important;
    outline: none !important;
}}
[data-baseweb="select"] > div {{
    background-color:{INPUT_BG} !important;
    border-color:{BORDER} !important;
    color:{TEXT} !important;
    border-radius:8px !important;
    font-size:13px !important;
}}
[data-baseweb="menu"]   {{ background-color:{CARD} !important; border:1px solid {BORDER} !important; border-radius:8px !important; }}
[data-baseweb="option"] {{ background-color:{CARD} !important; color:{TEXT} !important; font-size:13px !important; }}
[data-baseweb="option"]:hover {{ background-color:{THM_BG} !important; }}

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div > div {{
    background: {ACCENT} !important;
}}

/* ── Tous les boutons — base neutre ── */
.stButton > button {{
    font-family:'Inter',sans-serif !important;
    border-radius:8px !important;
    font-weight:500 !important;
    transition:all 0.18s ease !important;
    background:{THM_BG} !important;
    color:{TEXT} !important;
    border:1px solid {BORDER} !important;
    font-size:13px !important;
    padding: 6px 14px !important;
}}
.stButton > button:hover {{
    filter:brightness(1.1) !important;
    box-shadow:0 2px 10px rgba(0,0,0,0.15) !important;
}}

/* ── BOUTON SIMULATION — bleu royal, grand, glow ── */
button[data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, {SIM_BG} 0%, {SIM_HOVER} 100%) !important;
    color: {SIM_TXT} !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 0.08em !important;
    padding: 16px 0 !important;
    box-shadow: 0 4px 24px {SIM_GLOW}, 0 1px 3px rgba(0,0,0,0.2) !important;
    text-transform: uppercase !important;
    position: relative !important;
    overflow: hidden !important;
}}
button[data-testid="baseButton-primary"]:hover {{
    background: linear-gradient(135deg, {SIM_HOVER} 0%, {SIM_BG} 100%) !important;
    box-shadow: 0 8px 32px {SIM_GLOW}, 0 2px 6px rgba(0,0,0,0.25) !important;
    transform: translateY(-2px) !important;
}}
button[data-testid="baseButton-primary"]:active {{
    transform: translateY(1px) !important;
    box-shadow: 0 2px 12px {SIM_GLOW} !important;
}}

/* ── Alertes ── */
[data-testid="stAlert"] {{ border-radius:10px !important; }}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{ border-radius:10px !important; overflow:hidden; }}
thead tr th {{ background:{CARD} !important; color:{TEXT2} !important; font-size:11px !important; text-transform:uppercase; letter-spacing:0.05em; }}
tbody tr:hover td {{ background:{THM_BG} !important; }}

/* ── Info / success boxes ── */
[data-testid="stInfo"] {{
    background:{METRIC_BG} !important;
    border-left:3px solid {ACCENT} !important;
    border-radius:8px !important;
}}
[data-testid="stInfo"] p {{ color:{TEXT} !important; font-size:13px !important; }}

/* ── Divider ── */
[data-testid="stDivider"] hr {{ border-color:{HR} !important; }}

/* ── Scrollbar fine ── */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:{BORDER}; border-radius:3px; }}
</style>
""", unsafe_allow_html=True)


# ── Hash des paramètres ───────────────────────────────────────────────────────
def params_hash() -> str:
    snap = {k: str(st.session_state.get(k)) for k in [
        "system_voltage","pv_model","pv_technology","psh",
        "autonomy_days","loads",
    ]}
    return hashlib.md5(json.dumps(snap, sort_keys=True).encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
_, col_hdr, col_thm = st.columns([0.5, 8, 2])

with col_hdr:
    st.markdown(f"""
    <div style="text-align:center; padding:8px 0 6px 0;">
        <div style="font-size:46px; line-height:1; margin-bottom:6px;">⚡</div>
        <div style="font-family:'IBM Plex Mono',monospace; font-size:30px;
                    font-weight:700; letter-spacing:0.12em; color:{TEXT}; margin-bottom:4px;">
            PV SIZING
        </div>
        <div style="font-size:12px; color:{TEXT2}; letter-spacing:0.02em;">
            Plateforme de dimensionnement de systèmes photovoltaïques autonomes
        </div>
    </div>""", unsafe_allow_html=True)

with col_thm:
    st.markdown("<div style='height:34px'></div>", unsafe_allow_html=True)
    if st.button(f"{ICON_MODE}  {LBL_MODE}", key="toggle_theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

st.markdown(f"<hr style='border-color:{HR}; margin:14px 0 28px 0;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════════
render_parametres(TEXT=TEXT, TEXT2=TEXT2, ACCENT=ACCENT, CARD=CARD, BORDER=BORDER)

# Reset résultats si params ont changé après une simulation
if params_hash() != st.session_state.last_params_hash and st.session_state.show_results:
    st.session_state.show_results = False

st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BOUTON SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
_, col_sim, _ = st.columns([1, 4, 1])
with col_sim:
    if st.button("▶  Lancer la simulation", key="btn_simulation",
                 use_container_width=True, type="primary"):
        st.session_state.show_results     = True
        st.session_state.last_params_hash = params_hash()
        st.rerun()

# Message discret si les paramètres ont changé
if not st.session_state.show_results and st.session_state.last_params_hash != "":
    _, col_msg, _ = st.columns([1, 4, 1])
    with col_msg:
        st.markdown(
            f"<p style='text-align:center; font-size:11px; color:{TEXT2}; margin-top:7px;'>"
            "⟳ Paramètres modifiés — relancez la simulation pour voir les nouveaux résultats."
            "</p>", unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TABLEAU DE BORD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.show_results:
    st.markdown(f"<hr style='border-color:{HR}; margin:0 0 30px 0;'>", unsafe_allow_html=True)
    params  = get_params()
    results = run_sizing(params)
    render_dashboard(results, params,
                     dark_mode=st.session_state.dark_mode,
                     TEXT=TEXT, TEXT2=TEXT2, ACCENT=ACCENT, CARD=CARD, BORDER=BORDER)

    # ── Téléchargement des documents ──────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:10px;font-weight:700;letter-spacing:0.08em;color:{TEXT2};"
                f"text-transform:uppercase;margin-bottom:10px;'>DOCUMENTS À TÉLÉCHARGER</p>",
                unsafe_allow_html=True)

    _stamp      = datetime.now().strftime("%Y%m%d_%H%M")
    technical_pdf = generate_technical_pdf(results, params)
    client_pdf    = generate_client_pdf(results, params)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "📄  Fiche technique (PDF)",
            data=technical_pdf,
            file_name=f"pv_sizing_fiche_technique_{_stamp}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            "📑  Fiche de dimensionnement client (PDF)",
            data=client_pdf,
            file_name=f"pv_sizing_dimensionnement_client_{_stamp}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PIED DE PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"<p style='text-align:center; font-size:11px; color:{TEXT2}; margin-top:52px; line-height:1.8;'>"
    "PV Sizing v1.2 &nbsp;·&nbsp; Coefficient de performance PR = 0.75 &nbsp;·&nbsp; "
    "Résultats indicatifs — consultez un installateur certifié pour un dimensionnement définitif."
    "</p>", unsafe_allow_html=True)