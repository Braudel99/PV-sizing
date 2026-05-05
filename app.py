# app.py — Point d'entrée principal de la plateforme PV Sizing
import streamlit as st
import hashlib, json
from parametres import init_session_state, get_params, render_parametres
from dashboard  import render_dashboard
from engines    import run_sizing

# ── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(
    page_title="PV Sizing — Dimensionnement solaire",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Initialisation des états ──────────────────────────────────────────────────
init_session_state()

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "last_params_hash" not in st.session_state:
    st.session_state.last_params_hash = ""


# ── Palette sobre & désaturée ────────────────────────────────────────────────
# Mode sombre : bleu-gris ardoise, pas de noir pur
# Mode clair  : gris perle / blanc cassé, pas de blanc pur
if st.session_state.dark_mode:
    BG        = "#181C24"      # ardoise foncé, pas noir
    CARD      = "#1F2433"      # ardoise moyen
    TEXT      = "#CDD1DC"      # blanc cassé légèrement bleuté
    TEXT2     = "#7A8299"      # gris-bleu discret
    BORDER    = "#2C3245"      # bordure subtile
    INPUT_BG  = "#161A26"      # input légèrement plus sombre
    ACCENT    = "#7B9ED4"      # bleu acier doux — pas orange vif
    SIM_BG    = "#3D5A8A"      # bleu marine sobre
    SIM_TXT   = "#E8ECF4"
    THM_BG    = "#2C3245"
    THM_TXT   = "#CDD1DC"
    METRIC_BG = "rgba(255,255,255,0.03)"
    METRIC_BD = "rgba(255,255,255,0.07)"
    HR        = "rgba(255,255,255,0.06)"
    SHADOW    = "0 2px 14px rgba(0,0,0,0.4)"
    ICON_MODE = "☀️"
    LBL_MODE  = "Mode clair"
else:
    BG        = "#ECEEF4"      # gris perle froid
    CARD      = "#F6F7FA"      # blanc cassé
    TEXT      = "#2A2F3E"      # quasi-noir bleuté
    TEXT2     = "#6B7186"      # gris moyen lisible
    BORDER    = "#D4D7E3"      # bordure très légère
    INPUT_BG  = "#FFFFFF"
    ACCENT    = "#4A6FA5"      # bleu acier sobre
    SIM_BG    = "#3D5A8A"      # bleu marine sobre
    SIM_TXT   = "#FFFFFF"
    THM_BG    = "#DDE0EA"
    THM_TXT   = "#2A2F3E"
    METRIC_BG = "rgba(0,0,0,0.025)"
    METRIC_BD = "rgba(0,0,0,0.06)"
    HR        = "rgba(0,0,0,0.07)"
    SHADOW    = "0 2px 12px rgba(0,0,0,0.07)"
    ICON_MODE = "🌙"
    LBL_MODE  = "Mode sombre"

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

html, body, .stApp, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT} !important;
}}

.block-container {{
    max-width: 860px !important;
    margin: 0 auto !important;
    padding-top: 1.8rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}}

h1, h2, h3 {{
    font-family: 'IBM Plex Mono', monospace !important;
    color: {TEXT} !important;
}}
p, .stMarkdown p, label, .stCaption, small {{
    color: {TEXT2} !important;
}}

hr {{ border-color: {HR} !important; margin: 18px 0 !important; }}

/* Métriques */
[data-testid="metric-container"] {{
    background: {METRIC_BG} !important;
    border: 1px solid {METRIC_BD} !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
}}
[data-testid="stMetricValue"] {{
    color: {ACCENT} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 20px !important;
}}
[data-testid="stMetricLabel"] {{ color: {TEXT2} !important; font-size: 11px !important; }}
[data-testid="stMetricDelta"] {{ font-size: 11px !important; }}

/* Expanders */
[data-testid="stExpander"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    box-shadow: {SHADOW} !important;
    margin-bottom: 12px !important;
}}
details summary span {{
    font-weight: 600 !important;
    color: {TEXT} !important;
    font-size: 14px !important;
}}

/* Inputs */
input[type="text"], input[type="number"], textarea {{
    background-color: {INPUT_BG} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 7px !important;
}}
[data-baseweb="select"] > div {{
    background-color: {INPUT_BG} !important;
    border-color: {BORDER} !important;
    color: {TEXT} !important;
    border-radius: 7px !important;
}}
[data-baseweb="menu"] {{
    background-color: {CARD} !important;
    border: 1px solid {BORDER} !important;
}}
[data-baseweb="option"] {{
    background-color: {CARD} !important;
    color: {TEXT} !important;
}}
[data-baseweb="option"]:hover {{ background-color: {THM_BG} !important; }}

/* Tous les boutons — base neutre */
.stButton > button {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    border-radius: 7px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    background: {THM_BG} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    font-size: 13px !important;
}}
.stButton > button:hover {{
    filter: brightness(1.08) !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15) !important;
}}

/* Bouton simulation — bleu sobre */
[data-testid="stButton"]:has(button[data-testid="baseButton-primary"]) button {{
    background: {SIM_BG} !important;
    color: {SIM_TXT} !important;
    border: none !important;
    border-radius: 9px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 0.05em !important;
    padding: 13px 0 !important;
    box-shadow: 0 3px 16px rgba(61,90,138,0.35) !important;
}}
[data-testid="stButton"]:has(button[data-testid="baseButton-primary"]) button:hover {{
    filter: brightness(1.12) !important;
    box-shadow: 0 6px 22px rgba(61,90,138,0.45) !important;
    transform: translateY(-1px) !important;
}}

/* Alertes */
[data-testid="stAlert"] {{ border-radius: 9px !important; }}

/* Dataframe */
[data-testid="stDataFrame"] {{ border-radius: 9px !important; overflow: hidden; }}

/* Info boxes */
[data-testid="stInfo"] {{
    background: {METRIC_BG} !important;
    border-left: 3px solid {ACCENT} !important;
    border-radius: 7px !important;
}}
[data-testid="stInfo"] p {{ color: {TEXT} !important; }}
</style>
""", unsafe_allow_html=True)


# ── Fonction de hash des paramètres (pour détecter un changement) ─────────────
def params_hash() -> str:
    """Retourne un hash court des paramètres courants."""
    snapshot = {
        "pv_model":       st.session_state.get("pv_model"),
        "pv_count":       st.session_state.get("pv_count"),
        "psh":            st.session_state.get("psh"),
        "bat_model":      st.session_state.get("bat_model"),
        "bat_count":      st.session_state.get("bat_count"),
        "system_voltage": st.session_state.get("system_voltage"),
        "autonomy_days":  st.session_state.get("autonomy_days"),
        "reg_model":      st.session_state.get("reg_model"),
        "inv_model":      st.session_state.get("inv_model"),
        "loads":          str(st.session_state.get("loads", [])),
    }
    return hashlib.md5(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER CENTRÉ
# ═══════════════════════════════════════════════════════════════════════════════
_, col_hdr, col_thm = st.columns([0.5, 8, 2])

with col_hdr:
    st.markdown(
        f"""
        <div style="text-align:center; padding:6px 0 4px 0;">
            <div style="font-size:44px; line-height:1;">⚡</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:28px;
                        font-weight:700; letter-spacing:0.1em; color:{TEXT}; margin:7px 0 3px 0;">
                PV SIZING
            </div>
            <div style="font-size:12px; color:{TEXT2}; font-style:italic; line-height:1.5;">
                Plateforme de dimensionnement de systèmes photovoltaïques autonomes
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_thm:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    if st.button(f"{ICON_MODE}  {LBL_MODE}", key="toggle_theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

st.markdown(f"<hr style='border-color:{HR}; margin:16px 0 26px 0;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════════

# Hash AVANT le rendu des widgets (état précédent)
hash_before = params_hash()

render_parametres(TEXT=TEXT, TEXT2=TEXT2, ACCENT=ACCENT)

# Hash APRÈS (état courant — modifié si l'utilisateur a changé quelque chose)
hash_after = params_hash()

# Si les paramètres ont changé depuis la dernière simulation → on cache les résultats
if hash_after != st.session_state.last_params_hash and st.session_state.show_results:
    st.session_state.show_results = False

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BOUTON SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
_, col_sim, _ = st.columns([1, 4, 1])
with col_sim:
    clicked = st.button(
        "▶  Lancer la simulation",
        key="btn_simulation",
        use_container_width=True,
        type="primary",
    )
    if clicked:
        st.session_state.show_results = True
        st.session_state.last_params_hash = params_hash()
        st.rerun()

# Message d'invite si les paramètres ont été modifiés après une simulation
if not st.session_state.show_results and st.session_state.last_params_hash != "":
    _, col_msg, _ = st.columns([1, 4, 1])
    with col_msg:
        st.markdown(
            f"<p style='text-align:center; font-size:12px; color:{TEXT2}; margin-top:8px;'>"
            "⟳ Paramètres modifiés — relancez la simulation pour mettre à jour les résultats."
            "</p>",
            unsafe_allow_html=True
        )

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TABLEAU DE BORD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.show_results:
    st.markdown(f"<hr style='border-color:{HR}; margin:0 0 28px 0;'>", unsafe_allow_html=True)
    params  = get_params()
    results = run_sizing(params)
    render_dashboard(
        results, params,
        dark_mode=st.session_state.dark_mode,
        TEXT=TEXT, TEXT2=TEXT2, ACCENT=ACCENT, CARD=CARD, BORDER=BORDER,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PIED DE PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"<p style='text-align:center; font-size:11px; color:{TEXT2}; margin-top:48px;'>"
    "PV Sizing v1.0 &nbsp;·&nbsp; PR = 0.75 &nbsp;·&nbsp; "
    "Résultats indicatifs — consultez un installateur certifié pour un dimensionnement définitif."
    "</p>",
    unsafe_allow_html=True
)