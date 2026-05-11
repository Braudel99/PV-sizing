# parametres.py — Panneau de paramétrage  (v1.2)
import streamlit as st
from data import (
    PV_CATALOG, BATTERY_CATALOG, REGULATOR_CATALOG, INVERTER_CATALOG,
    DEFAULT_LOADS, PSH_DEFAULT,
    batteries_for_voltage, inverters_for_voltage,
)


def init_session_state():
    defaults = {
        "system_voltage": 12,
        "pv_model":       "Mono 100 Wc",
        "pv_technology":  "Monocristallin",
        "pv_count":       2,
        "psh":            PSH_DEFAULT,
        "bat_model":      "12V — 100 Ah AGM",
        "bat_count":      2,
        "autonomy_days":  1,          # ← défaut 1 jour
        "reg_model":      "[MPPT] 20A — 100V",
        "inv_model":      "12V —  500 W (Onde pure)",
        "loads":          [dict(l) for l in DEFAULT_LOADS],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


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


def _ensure_compatible_models():
    """Remet batterie/onduleur sur le premier compatible après changement de tension."""
    v = st.session_state.system_voltage
    bat_opts = list(batteries_for_voltage(v).keys())
    inv_opts = list(inverters_for_voltage(v).keys())
    if st.session_state.bat_model not in bat_opts and bat_opts:
        st.session_state.bat_model = bat_opts[0]
    if st.session_state.inv_model not in inv_opts and inv_opts:
        st.session_state.inv_model = inv_opts[0]


def _section_label(text: str, TEXT2: str) -> None:
    st.markdown(
        f"<p style='font-size:10px; font-weight:700; letter-spacing:0.08em; "
        f"color:{TEXT2}; text-transform:uppercase; margin:0 0 10px 0;'>{text}</p>",
        unsafe_allow_html=True,
    )


def render_parametres(TEXT="#CDD1DC", TEXT2="#7A8299", ACCENT="#7B9ED4",
                      CARD="#1F2433", BORDER="#2C3245"):

    st.markdown(
        "<h2 style='text-align:center; font-size:20px; margin-bottom:4px;'>⚙️ Paramètres du système</h2>"
        "<p style='text-align:center; font-size:12px; margin-bottom:24px;'>"
        "Configurez chaque composant puis lancez la simulation.</p>",
        unsafe_allow_html=True,
    )

    # ════════════════════════════════════════════════════════════════════════
    # 1. PANNEAUX PV + TENSION SYSTÈME
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("☀️  Panneaux photovoltaïques", expanded=True):

        # ── Tension + Technologie ────────────────────────────────────────────
        _section_label("Paramètres système", TEXT2)
        cv, ct = st.columns(2)

        with cv:
            new_v = st.selectbox(
                "🔌 Tension du système",
                options=[12, 24, 48],
                index=[12, 24, 48].index(st.session_state.system_voltage),
                key="sel_sysv",
                format_func=lambda x: f"{x} V",
                help="Détermine les batteries et onduleurs compatibles. Choisissez avant tout autre paramètre.",
            )
            if new_v != st.session_state.system_voltage:
                st.session_state.system_voltage = new_v
                _ensure_compatible_models()
                st.rerun()

        with ct:
            tech = st.selectbox(
                "🔬 Technologie",
                options=["Monocristallin", "Polycristallin"],
                index=["Monocristallin","Polycristallin"].index(st.session_state.pv_technology),
                key="sel_pv_tech",
                help="Monocristallin : rendement ~18–22 %, meilleur en faible luminosité.\n"
                     "Polycristallin : rendement ~15–18 %, coût plus faible.",
            )
            st.session_state.pv_technology = tech

        # Bandeau info tension — compact
        st.markdown(
            f"<div style='background:rgba(123,158,212,0.08); border:1px solid rgba(123,158,212,0.2); "
            f"border-radius:8px; padding:8px 12px; font-size:12px; color:{TEXT2}; margin:10px 0;'>"
            f"🔒 Tension <strong style='color:{ACCENT}'>{st.session_state.system_voltage} V</strong> — "
            f"Batteries et onduleurs filtrés automatiquement."
            f"</div>",
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Modèle + Nombre ──────────────────────────────────────────────────
        _section_label("Champ photovoltaïque", TEXT2)
        col1, col2 = st.columns(2)

        with col1:
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
            st.caption(f"Voc {panel['voc']} V · Isc {panel['isc']} A · Vmp {panel['vmp']} V · Imp {panel['imp']} A")

        with col2:
            st.session_state.pv_count = st.number_input(
                "Nombre de panneaux", min_value=1, max_value=50,
                value=st.session_state.pv_count, key="ni_pv_count",
            )
            panel    = PV_CATALOG[st.session_state.pv_model]
            peak_wc  = panel["power"] * st.session_state.pv_count
            from data import PERFORMANCE_RATIO
            est_wh   = peak_wc * st.session_state.psh * PERFORMANCE_RATIO
            st.metric("Puissance crête totale", f"{peak_wc} Wc",
                      delta=f"≈ {est_wh:.0f} Wh/j estimés")

        # ── PSH ───────────────────────────────────────────────────────────────
        st.session_state.psh = st.slider(
            "☀ Heures de soleil pic (PSH)",
            min_value=1.0, max_value=10.0,
            value=float(st.session_state.psh), step=0.5,
            key="sl_psh",
            help="Irradiation journalière équivalente à 1000 W/m² · Afrique de l'Ouest : 4–6h · Europe : 2.5–4h",
        )

    # ════════════════════════════════════════════════════════════════════════
    # 2. BATTERIES
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🔋  Batteries", expanded=True):
        v        = st.session_state.system_voltage
        bat_opts = list(batteries_for_voltage(v).keys())

        _section_label(f"Batteries {v} V uniquement", TEXT2)

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.bat_model = st.selectbox(
                "Modèle de batterie", options=bat_opts,
                index=bat_opts.index(st.session_state.bat_model) if st.session_state.bat_model in bat_opts else 0,
                key="sel_bat_model",
            )
            bat = BATTERY_CATALOG[st.session_state.bat_model]
            # Fiche technique compacte
            st.markdown(
                f"<div style='background:rgba(123,158,212,0.06); border-radius:7px; "
                f"padding:8px 10px; font-size:12px; color:{TEXT2}; margin-top:4px;'>"
                f"<b>Techno :</b> {bat['technology']} &nbsp;·&nbsp; "
                f"<b>DoD :</b> {int(bat['dod']*100)}% &nbsp;·&nbsp; "
                f"<b>Cycles :</b> {bat['cycles']}"
                f"</div>", unsafe_allow_html=True)

        with col2:
            st.session_state.bat_count = st.number_input(
                "Nombre de batteries", min_value=1, max_value=20,
                value=st.session_state.bat_count, key="ni_bat_count",
            )
            bat    = BATTERY_CATALOG[st.session_state.bat_model]
            usable = bat["capacity"] * st.session_state.bat_count * v * bat["dod"]
            total  = bat["capacity"] * st.session_state.bat_count * v
            st.metric("Capacité utile", f"{usable:.0f} Wh",
                      delta=f"Totale : {total:.0f} Wh")

        # Autonomie avec indication contextuelle
        st.session_state.autonomy_days = st.slider(
            "⏳ Autonomie souhaitée",
            min_value=1, max_value=7,
            value=st.session_state.autonomy_days,
            key="sl_auto",
            format="%d jour(s)",
            help="Nombre de jours sans soleil à couvrir. 1 jour = usage courant, 3+ jours = zone nuageuse fréquente.",
        )
        # Capacité nécessaire estimée
        loads = st.session_state.loads
        total_wh_loads = sum(
            float(l["power"]) * (
                (l.get("end_h", 22) - l.get("start_h", 6))
                if l.get("end_h", 22) > l.get("start_h", 6)
                else (24 - l.get("start_h", 6) + l.get("end_h", 22))
            ) for l in loads
        )
        required = total_wh_loads * st.session_state.autonomy_days
        bat_ok   = usable >= required
        status_color = ACCENT if bat_ok else "#C0504A"
        status_icon  = "✓" if bat_ok else "⚠"
        st.markdown(
            f"<div style='font-size:12px; color:{status_color}; margin-top:6px;'>"
            f"{status_icon} Capacité requise : <strong>{required:.0f} Wh</strong> — "
            f"disponible : <strong>{usable:.0f} Wh</strong>"
            f"{'  →  OK' if bat_ok else '  →  Insuffisant, augmentez le nombre de batteries'}"
            f"</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 3. RÉGULATEUR
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("⚡  Régulateur de charge", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            reg_keys = list(REGULATOR_CATALOG.keys())
            st.session_state.reg_model = st.selectbox(
                "Modèle", options=reg_keys,
                index=reg_keys.index(st.session_state.reg_model),
                key="sel_reg",
                help="MPPT : +25–30 % d'énergie récupérée vs PWM. Indispensable pour les grandes installations.",
            )
        with col2:
            reg = REGULATOR_CATALOG[st.session_state.reg_model]
            # Calcul du courant PV en temps réel pour vérification immédiate
            panel    = PV_CATALOG[st.session_state.pv_model]
            pv_curr  = panel["imp"] * st.session_state.pv_count * 1.25
            curr_ok  = pv_curr <= reg["current_max"]
            curr_color = ACCENT if curr_ok else "#C0504A"
            st.markdown(
                f"<div style='background:rgba(123,158,212,0.06); border-radius:8px; "
                f"padding:10px 12px; font-size:12px; color:{TEXT2};'>"
                f"<b>{reg['type']}</b> · {reg['current_max']} A max · {reg['voltage_max']} V max · "
                f"Rdt {int(reg['efficiency']*100)} %<br>"
                f"<span style='color:{curr_color}; font-weight:600;'>"
                f"{'✓' if curr_ok else '⚠'} Courant PV requis : {pv_curr:.1f} A"
                f"{'  →  OK' if curr_ok else '  →  Régulateur insuffisant'}"
                f"</span></div>",
                unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 4. ONDULEUR
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🔌  Onduleur", expanded=True):
        v        = st.session_state.system_voltage
        inv_opts = list(inverters_for_voltage(v).keys())

        _section_label(f"Onduleurs {v} V DC uniquement", TEXT2)

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.inv_model = st.selectbox(
                "Modèle", options=inv_opts,
                index=inv_opts.index(st.session_state.inv_model) if st.session_state.inv_model in inv_opts else 0,
                key="sel_inv",
                help="Choisissez un onduleur dont la puissance nominale dépasse la somme des charges simultanées.",
            )
        with col2:
            inv       = INVERTER_CATALOG[st.session_state.inv_model]
            peak_load = sum(float(l["power"]) for l in st.session_state.loads)
            inv_ok    = peak_load <= inv["power"]
            inv_color = ACCENT if inv_ok else "#C0504A"
            st.markdown(
                f"<div style='background:rgba(123,158,212,0.06); border-radius:8px; "
                f"padding:10px 12px; font-size:12px; color:{TEXT2};'>"
                f"<b>{inv['power']} W</b> nominal · Crête {inv['power_peak']} W<br>"
                f"DC {inv['input_v']} V · Onde {inv['wave']} · Rdt {int(inv['efficiency']*100)} %<br>"
                f"<span style='color:{inv_color}; font-weight:600;'>"
                f"{'✓' if inv_ok else '⚠'} Charge totale : {peak_load:.0f} W"
                f"{'  →  OK' if inv_ok else '  →  Onduleur insuffisant'}"
                f"</span></div>",
                unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 5. CHARGES
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("💡  Charges & appareils", expanded=True):
        st.caption("Puissance (W) · Heure début et fin d'utilisation (0–23h). Passage minuit supporté.")

        loads = st.session_state.loads

        # En-têtes colonnes
        h1, h2, h3, h4, h5 = st.columns([2.8, 1.1, 1.0, 1.0, 0.45])
        for col, lbl in zip([h1, h2, h3, h4], ["Appareil", "W", "Début", "Fin"]):
            col.markdown(f"<span style='font-size:10px;color:{TEXT2};font-weight:600;text-transform:uppercase;'>{lbl}</span>",
                         unsafe_allow_html=True)

        to_delete = []
        for i, load in enumerate(loads):
            c1, c2, c3, c4, c5 = st.columns([2.8, 1.1, 1.0, 1.0, 0.45])
            with c1:
                loads[i]["name"] = st.text_input(f"n{i}", value=load["name"],
                                                  label_visibility="collapsed", key=f"lname_{i}")
            with c2:
                loads[i]["power"] = st.number_input(f"w{i}", value=float(load["power"]),
                                                     min_value=0.0, max_value=10000.0, step=10.0,
                                                     label_visibility="collapsed", key=f"lpow_{i}")
            with c3:
                loads[i]["start_h"] = st.number_input(f"s{i}", value=int(load.get("start_h", 6)),
                                                       min_value=0, max_value=23, step=1,
                                                       label_visibility="collapsed", key=f"lstart_{i}")
            with c4:
                loads[i]["end_h"] = st.number_input(f"e{i}", value=int(load.get("end_h", 22)),
                                                     min_value=0, max_value=23, step=1,
                                                     label_visibility="collapsed", key=f"lend_{i}")
            with c5:
                if st.button("✕", key=f"del_{i}", help="Supprimer"):
                    to_delete.append(i)

            # Feedback immédiat : durée + Wh
            s   = int(loads[i].get("start_h", 6))
            e   = int(loads[i].get("end_h", 22))
            dur = (e - s) if e > s else (24 - s + e) if e < s else 0
            wh  = float(loads[i]["power"]) * dur
            c1.markdown(
                f"<span style='font-size:10px; color:{TEXT2};'>⏱ {dur}h · {wh:.0f} Wh/j</span>",
                unsafe_allow_html=True)

        for idx in reversed(to_delete):
            loads.pop(idx)
        st.session_state.loads = loads

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("＋  Ajouter un appareil", use_container_width=True):
            st.session_state.loads.append({"name": "Nouvel appareil", "power": 0.0,
                                            "start_h": 8, "end_h": 20})
            st.rerun()

        # Totaux avec barre de progression visuelle
        total_wh = sum(
            float(l["power"]) * (
                (l.get("end_h",22) - l.get("start_h",6))
                if l.get("end_h",22) > l.get("start_h",6)
                else (24 - l.get("start_h",6) + l.get("end_h",22))
            ) for l in loads
        )
        total_w = sum(float(l["power"]) for l in loads)
        st.divider()
        ct1, ct2 = st.columns(2)
        ct1.metric("⚡ Énergie journalière", f"{total_wh:.0f} Wh/j")
        ct2.metric("🔺 Puissance de pointe", f"{total_w:.0f} W")