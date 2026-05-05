# parametres.py — Panneau de paramétrage
import streamlit as st
from data import (
    PV_CATALOG, BATTERY_CATALOG, REGULATOR_CATALOG,
    INVERTER_CATALOG, DEFAULT_LOADS, PSH_DEFAULT
)


def init_session_state():
    defaults = {
        "pv_model":       "Panneau 100 Wc",
        "pv_count":       2,
        "psh":            PSH_DEFAULT,
        "bat_model":      "Batterie 100 Ah — AGM",
        "bat_count":      2,
        "system_voltage": 12,
        "autonomy_days":  3,
        "reg_model":      "[MPPT] 20A — 100V",
        "inv_model":      "Onduleur  500 W — 12V (Onde pure)",
        "loads":          [dict(l) for l in DEFAULT_LOADS],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_params() -> dict:
    return {
        "panel":          PV_CATALOG.get(st.session_state.pv_model),
        "pv_count":       st.session_state.pv_count,
        "psh":            st.session_state.psh,
        "battery":        BATTERY_CATALOG.get(st.session_state.bat_model),
        "bat_count":      st.session_state.bat_count,
        "system_voltage": st.session_state.system_voltage,
        "autonomy_days":  st.session_state.autonomy_days,
        "regulator":      REGULATOR_CATALOG.get(st.session_state.reg_model),
        "inverter":       INVERTER_CATALOG.get(st.session_state.inv_model),
        "loads":          st.session_state.loads,
    }


def render_parametres(TEXT="#CDD1DC", TEXT2="#7A8299", ACCENT="#7B9ED4"):

    st.markdown(
        f"<h2 style='text-align:center; font-size:20px; margin-bottom:4px;'>⚙️ Paramètres du système</h2>"
        f"<p style='text-align:center; font-size:12px; margin-bottom:22px;'>"
        f"Configurez chaque composant puis lancez la simulation.</p>",
        unsafe_allow_html=True
    )

    # ── PV ────────────────────────────────────────────────────────────────────
    with st.expander("☀️  Panneaux photovoltaïques", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.pv_model = st.selectbox(
                "Modèle de panneau",
                options=list(PV_CATALOG.keys()),
                index=list(PV_CATALOG.keys()).index(st.session_state.pv_model),
                key="sel_pv_model",
                help="Puissance crête du panneau solaire"
            )
            panel = PV_CATALOG[st.session_state.pv_model]
            st.caption(
                f"Voc {panel['voc']} V · Isc {panel['isc']} A · "
                f"Vmp {panel['vmp']} V · Imp {panel['imp']} A"
            )
        with col2:
            st.session_state.pv_count = st.number_input(
                "Nombre de panneaux", min_value=1, max_value=50,
                value=st.session_state.pv_count, key="ni_pv_count"
            )
            panel = PV_CATALOG[st.session_state.pv_model]
            st.metric("Puissance crête totale", f"{panel['power'] * st.session_state.pv_count} Wc")

        st.session_state.psh = st.slider(
            "Heures de soleil pic (PSH)",
            min_value=1.0, max_value=10.0,
            value=float(st.session_state.psh), step=0.5,
            key="sl_psh",
            help="Heures équivalentes à 1000 W/m² par jour — typiquement 4–6h en Afrique de l'Ouest"
        )

    # ── Batteries ─────────────────────────────────────────────────────────────
    with st.expander("🔋  Batteries", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.bat_model = st.selectbox(
                "Modèle de batterie",
                options=list(BATTERY_CATALOG.keys()),
                index=list(BATTERY_CATALOG.keys()).index(st.session_state.bat_model),
                key="sel_bat_model"
            )
            bat = BATTERY_CATALOG[st.session_state.bat_model]
            st.caption(f"Techno : {bat['technology']} · DoD max : {int(bat['dod']*100)}% · Cycles : {bat['cycles']}")
        with col2:
            st.session_state.bat_count = st.number_input(
                "Nombre de batteries", min_value=1, max_value=20,
                value=st.session_state.bat_count, key="ni_bat_count"
            )
            bat     = BATTERY_CATALOG[st.session_state.bat_model]
            usable  = bat["capacity"] * st.session_state.bat_count * st.session_state.system_voltage * bat["dod"]
            st.metric("Capacité utile totale", f"{usable:.0f} Wh")

        col3, col4 = st.columns(2)
        with col3:
            st.session_state.system_voltage = st.selectbox(
                "Tension du système (V)", options=[12, 24, 48],
                index=[12, 24, 48].index(st.session_state.system_voltage),
                key="sel_sysv"
            )
        with col4:
            st.session_state.autonomy_days = st.slider(
                "Autonomie souhaitée (jours)", min_value=1, max_value=7,
                value=st.session_state.autonomy_days, key="sl_auto",
                help="Jours consécutifs sans soleil à couvrir"
            )

    # ── Régulateur ────────────────────────────────────────────────────────────
    with st.expander("⚡  Régulateur de charge", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.reg_model = st.selectbox(
                "Modèle de régulateur",
                options=list(REGULATOR_CATALOG.keys()),
                index=list(REGULATOR_CATALOG.keys()).index(st.session_state.reg_model),
                key="sel_reg",
                help="MPPT : +25–30% rendement vs PWM"
            )
        with col2:
            reg = REGULATOR_CATALOG[st.session_state.reg_model]
            st.info(
                f"**{reg['type']}** · {reg['current_max']} A max · "
                f"{reg['voltage_max']} V max · Rdt {int(reg['efficiency']*100)}%"
            )

    # ── Onduleur ──────────────────────────────────────────────────────────────
    with st.expander("🔌  Onduleur", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.inv_model = st.selectbox(
                "Modèle d'onduleur",
                options=list(INVERTER_CATALOG.keys()),
                index=list(INVERTER_CATALOG.keys()).index(st.session_state.inv_model),
                key="sel_inv",
                help="Puissance nominale > puissance totale des charges"
            )
        with col2:
            inv = INVERTER_CATALOG[st.session_state.inv_model]
            st.info(
                f"**{inv['power']} W** nominal · Crête {inv['power_peak']} W · "
                f"DC {inv['input_v']} V · Onde {inv['wave']} · Rdt {int(inv['efficiency']*100)}%"
            )

    # ── Charges ───────────────────────────────────────────────────────────────
    with st.expander("💡  Charges & appareils", expanded=True):
        st.caption("Puissance en W · Durée en heures/jour")

        loads = st.session_state.loads

        h1, h2, h3, h4 = st.columns([3, 1.3, 1.3, 0.5])
        h1.markdown(f"<span style='font-size:11px;color:{TEXT2}'>Appareil</span>", unsafe_allow_html=True)
        h2.markdown(f"<span style='font-size:11px;color:{TEXT2}'>Puissance (W)</span>", unsafe_allow_html=True)
        h3.markdown(f"<span style='font-size:11px;color:{TEXT2}'>Durée (h/j)</span>", unsafe_allow_html=True)
        h4.markdown("&nbsp;", unsafe_allow_html=True)

        to_delete = []
        for i, load in enumerate(loads):
            c1, c2, c3, c4 = st.columns([3, 1.3, 1.3, 0.5])
            with c1:
                loads[i]["name"] = st.text_input(
                    f"n{i}", value=load["name"], label_visibility="collapsed", key=f"lname_{i}")
            with c2:
                loads[i]["power"] = st.number_input(
                    f"w{i}", value=float(load["power"]), min_value=0.0, max_value=10000.0,
                    step=10.0, label_visibility="collapsed", key=f"lpow_{i}")
            with c3:
                loads[i]["hours"] = st.number_input(
                    f"h{i}", value=float(load["hours"]), min_value=0.0, max_value=24.0,
                    step=0.5, label_visibility="collapsed", key=f"lhrs_{i}")
            with c4:
                if st.button("✕", key=f"del_{i}", help="Supprimer"):
                    to_delete.append(i)

        for idx in reversed(to_delete):
            loads.pop(idx)
        st.session_state.loads = loads

        if st.button("＋  Ajouter un appareil", use_container_width=True):
            st.session_state.loads.append({"name": "Nouvel appareil", "power": 0.0, "hours": 1.0})
            st.rerun()

        total_wh = sum(l["power"] * l["hours"] for l in loads)
        total_w  = sum(l["power"] for l in loads)
        st.divider()
        ct1, ct2 = st.columns(2)
        ct1.metric("⚡ Énergie journalière", f"{total_wh:.0f} Wh/j")
        ct2.metric("🔺 Puissance de pointe", f"{total_w:.0f} W")