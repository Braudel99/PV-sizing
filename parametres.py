# parametres.py — Panneau de paramétrage  (v1.4)
import streamlit as st
from data import PV_CATALOG, DEFAULT_LOADS, PSH_DEFAULT
from engines import total_load_power, total_load_daily_energy


def init_session_state():
    defaults = {
        "system_voltage": 12,
        "pv_model":       "Mono 100 Wc",
        "pv_technology":  "Monocristallin",
        "psh":            PSH_DEFAULT,
        "autonomy_days":  1,
        "loads":          [dict(l) for l in DEFAULT_LOADS],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_params() -> dict:
    return {
        "panel":          PV_CATALOG.get(st.session_state.pv_model),
        "pv_model_name":  st.session_state.pv_model,
        "pv_technology":  st.session_state.pv_technology,
        "psh":            st.session_state.psh,
        "system_voltage": st.session_state.system_voltage,
        "autonomy_days":  st.session_state.autonomy_days,
        "loads":          st.session_state.loads,
    }


def _section_label(text: str, TEXT2: str):
    st.markdown(
        f"<p style='font-size:10px;font-weight:700;letter-spacing:0.08em;"
        f"color:{TEXT2};text-transform:uppercase;margin:0 0 10px 0;'>{text}</p>",
        unsafe_allow_html=True,
    )


def _info_box(html: str, ACCENT: str):
    st.markdown(
        f"<div style='background:rgba(123,158,212,0.07);border:1px solid rgba(123,158,212,0.18);"
        f"border-radius:8px;padding:10px 13px;font-size:12px;line-height:1.7;'>{html}</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
def render_parametres(TEXT="#CDD1DC", TEXT2="#7A8299", ACCENT="#7B9ED4",
                      CARD="#1F2433", BORDER="#2C3245"):

    st.markdown(
        "<h2 style='text-align:center;font-size:20px;margin-bottom:4px;'>⚙️ Paramètres du système</h2>"
        "<p style='text-align:center;font-size:12px;margin-bottom:24px;'>"
        "Configurez les charges, puis les composants. Lancez ensuite la simulation.</p>",
        unsafe_allow_html=True,
    )

    # ════════════════════════════════════════════════════════════════════════
    # 0.  TENSION SYSTÈME  (choix global, en dehors des expanders, bien visible)
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='background:rgba(123,158,212,0.07);border:1px solid rgba(123,158,212,0.22);"
        f"border-radius:10px;padding:12px 18px;margin-bottom:18px;'>"
        f"<span style='font-size:11px;font-weight:700;letter-spacing:0.06em;color:{ACCENT};"
        f"text-transform:uppercase;'>🔌 Tension du système</span></div>",
        unsafe_allow_html=True,
    )
    col_v1, col_v2, col_v3 = st.columns([1, 2, 3])
    with col_v1:
        new_v = st.selectbox(
            "Tension (V)", options=[12, 24, 48],
            index=[12, 24, 48].index(st.session_state.system_voltage),
            key="sel_sysv",
            format_func=lambda x: f"{x} V",
            label_visibility="collapsed",
            help="Ce choix détermine automatiquement les batteries et onduleurs compatibles.",
        )
        if new_v != st.session_state.system_voltage:
            st.session_state.system_voltage = new_v
            st.rerun()
    with col_v2:
        st.markdown(
            f"<span style='font-size:12px;color:{ACCENT};font-weight:600;'>"
            f"🔒 Batterie, régulateur et onduleur seront choisis pour {st.session_state.system_voltage} V"
            f"</span>", unsafe_allow_html=True,
        )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 1.  CHARGES  (EN PREMIER)
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("💡  Charges & appareils", expanded=True):
        st.caption("Puissance unitaire (W) · Quantité (ex : 3 lampes) · Heure début → fin d'utilisation (0–23 h). Passage minuit supporté.")

        loads = st.session_state.loads

        h1, h2, h3, h4, h5, h6 = st.columns([2.4, 1.0, 0.7, 0.9, 0.9, 0.45])
        for col, lbl in zip([h1, h2, h3, h4, h5], ["Appareil", "W/unité", "Qté", "Début h", "Fin h"]):
            col.markdown(
                f"<span style='font-size:10px;color:{TEXT2};font-weight:700;"
                f"text-transform:uppercase;'>{lbl}</span>", unsafe_allow_html=True)

        to_delete = []
        for i, load in enumerate(loads):
            c1, c2, c3, c4, c5, c6 = st.columns([2.4, 1.0, 0.7, 0.9, 0.9, 0.45])
            with c1:
                loads[i]["name"] = st.text_input(f"n{i}", value=load["name"],
                                                  label_visibility="collapsed", key=f"lname_{i}")
            with c2:
                loads[i]["power"] = st.number_input(f"w{i}", value=float(load["power"]),
                                                     min_value=0.0, max_value=10000.0, step=10.0,
                                                     label_visibility="collapsed", key=f"lpow_{i}")
            with c3:
                loads[i]["qty"] = st.number_input(f"q{i}", value=int(load.get("qty", 1)),
                                                   min_value=1, max_value=100, step=1,
                                                   label_visibility="collapsed", key=f"lqty_{i}")
            with c4:
                loads[i]["start_h"] = st.number_input(f"s{i}", value=int(load.get("start_h", 6)),
                                                       min_value=0, max_value=23, step=1,
                                                       label_visibility="collapsed", key=f"lstart_{i}")
            with c5:
                loads[i]["end_h"] = st.number_input(f"e{i}", value=int(load.get("end_h", 22)),
                                                     min_value=0, max_value=23, step=1,
                                                     label_visibility="collapsed", key=f"lend_{i}")
            with c6:
                if st.button("✕", key=f"del_{i}", help="Supprimer"):
                    to_delete.append(i)

            # Feedback durée + Wh (quantité comprise)
            s   = int(loads[i].get("start_h", 6))
            e   = int(loads[i].get("end_h", 22))
            qty = int(loads[i].get("qty", 1))
            dur = (e - s) if e > s else (24 - s + e) if e < s else 0
            wh  = float(loads[i]["power"]) * qty * dur
            c1.markdown(f"<span style='font-size:10px;color:{TEXT2};'>⏱ {dur}h · {qty}× · {wh:.0f} Wh/j</span>",
                        unsafe_allow_html=True)

        for idx in reversed(to_delete):
            loads.pop(idx)
        st.session_state.loads = loads

        if st.button("＋  Ajouter un appareil", use_container_width=True):
            st.session_state.loads.append({"name": "Nouvel appareil", "power": 0.0, "qty": 1,
                                            "start_h": 8, "end_h": 20})
            st.rerun()

        # Totaux
        total_wh = total_load_daily_energy(loads)
        total_w  = total_load_power(loads)
        st.divider()
        ct1, ct2 = st.columns(2)
        ct1.metric("⚡ Énergie journalière", f"{total_wh:.0f} Wh/j")
        ct2.metric("🔺 Puissance de pointe", f"{total_w:.0f} W")

    # ════════════════════════════════════════════════════════════════════════
    # 2.  PANNEAUX PV  +  CÂBLAGE
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("☀️  Panneaux photovoltaïques", expanded=True):

        # ── Technologie ───────────────────────────────────────────────────────
        tech = st.selectbox(
            "🔬 Technologie",
            options=["Monocristallin", "Polycristallin"],
            index=["Monocristallin", "Polycristallin"].index(st.session_state.pv_technology),
            key="sel_pv_tech",
            help="Monocristallin : rendement 18–22 %. Polycristallin : rendement 15–18 %, moins cher.",
        )
        st.session_state.pv_technology = tech

        st.divider()

        # ── Modèle (puissance de panneau voulue) ──────────────────────────────
        _section_label("Puissance de panneau voulue", TEXT2)

        filtered_pv = {k: v for k, v in PV_CATALOG.items()
                       if v["technology"] == st.session_state.pv_technology}
        pv_keys = list(filtered_pv.keys())
        if st.session_state.pv_model not in pv_keys:
            st.session_state.pv_model = pv_keys[0]

        st.session_state.pv_model = st.selectbox(
            "Modèle de panneau", options=pv_keys,
            index=pv_keys.index(st.session_state.pv_model),
            key="sel_pv_model",
        )
        panel = PV_CATALOG[st.session_state.pv_model]
        st.caption(f"{panel['power']} Wc · Voc {panel['voc']} V · Isc {panel['isc']} A · "
                   f"Vmp {panel['vmp']} V · Imp {panel['imp']} A")

        st.markdown(
            f"<div style='background:rgba(123,158,212,0.07);border:1px solid rgba(123,158,212,0.18);"
            f"border-radius:8px;padding:10px 14px;font-size:12px;margin-top:8px;line-height:1.7;'>"
            f"Le nombre de panneaux et le montage (série/parallèle) sont calculés "
            f"automatiquement lors du lancement de la simulation, à partir de vos charges, "
            f"de la puissance de panneau choisie et de l'irradiation ci-dessous."
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── PSH ───────────────────────────────────────────────────────────────
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.session_state.psh = st.slider(
            "☀ Heures de soleil pic (PSH)",
            min_value=1.0, max_value=10.0,
            value=float(st.session_state.psh), step=0.5,
            key="sl_psh",
            help="Afrique de l'Ouest : 4–6 h · Europe : 2.5–4 h · Désert : 6–9 h",
        )

        # ── Autonomie batterie souhaitée ───────────────────────────────────────
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.session_state.autonomy_days = st.slider(
            "⏳ Autonomie batterie souhaitée",
            min_value=1, max_value=7, value=st.session_state.autonomy_days,
            key="sl_auto", format="%d jour(s)",
            help="1 j = usage normal · 3 j+ = zone souvent nuageuse",
        )

        st.markdown(
            f"<div style='background:rgba(123,158,212,0.07);border:1px solid rgba(123,158,212,0.18);"
            f"border-radius:8px;padding:10px 14px;font-size:12px;margin-top:8px;line-height:1.7;'>"
            f"Batterie, régulateur et onduleur sont choisis et dimensionnés automatiquement "
            f"lors du lancement de la simulation — retrouvez-les dans les résultats."
            f"</div>",
            unsafe_allow_html=True,
        )