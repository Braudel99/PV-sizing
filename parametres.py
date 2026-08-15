# parametres.py — Panneau de paramétrage  (v1.3)
import streamlit as st
from data import (
    PV_CATALOG, BATTERY_CATALOG, REGULATOR_CATALOG, INVERTER_CATALOG,
    DEFAULT_LOADS, PSH_DEFAULT, PERFORMANCE_RATIO,
    batteries_for_voltage, inverters_for_voltage, regulators_for_pv,
)
from engines import calc_pv_wiring


def init_session_state():
    defaults = {
        "system_voltage": 12,
        "pv_model":       "Mono 100 Wc",
        "pv_technology":  "Monocristallin",
        "pv_count":       2,
        "pv_wiring":      "parallel",      # défaut : parallèle
        "psh":            PSH_DEFAULT,
        "bat_model":      "12V — 100 Ah AGM",
        "bat_count":      2,
        "autonomy_days":  1,
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
        "pv_wiring":      st.session_state.pv_wiring,
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
    v        = st.session_state.system_voltage
    bat_opts = list(batteries_for_voltage(v).keys())
    inv_opts = list(inverters_for_voltage(v).keys())
    if st.session_state.bat_model not in bat_opts and bat_opts:
        st.session_state.bat_model = bat_opts[0]
    if st.session_state.inv_model not in inv_opts and inv_opts:
        st.session_state.inv_model = inv_opts[0]


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
            help="Ce choix verrouille les batteries et onduleurs compatibles.",
        )
        if new_v != st.session_state.system_voltage:
            st.session_state.system_voltage = new_v
            _ensure_compatible_models()
            st.rerun()
    with col_v2:
        st.markdown(
            f"<span style='font-size:12px;color:{ACCENT};font-weight:600;'>"
            f"🔒 Batteries et onduleurs filtrés sur {st.session_state.system_voltage} V"
            f"</span>", unsafe_allow_html=True,
        )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 1.  CHARGES  (EN PREMIER)
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("💡  Charges & appareils", expanded=True):
        st.caption("Puissance (W) · Heure début → fin d'utilisation (0–23 h). Passage minuit supporté.")

        loads = st.session_state.loads

        h1, h2, h3, h4, h5 = st.columns([2.8, 1.1, 1.0, 1.0, 0.45])
        for col, lbl in zip([h1, h2, h3, h4], ["Appareil", "W", "Début h", "Fin h"]):
            col.markdown(
                f"<span style='font-size:10px;color:{TEXT2};font-weight:700;"
                f"text-transform:uppercase;'>{lbl}</span>", unsafe_allow_html=True)

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

            # Feedback durée + Wh
            s   = int(loads[i].get("start_h", 6))
            e   = int(loads[i].get("end_h", 22))
            dur = (e - s) if e > s else (24 - s + e) if e < s else 0
            wh  = float(loads[i]["power"]) * dur
            c1.markdown(f"<span style='font-size:10px;color:{TEXT2};'>⏱ {dur}h · {wh:.0f} Wh/j</span>",
                        unsafe_allow_html=True)

        for idx in reversed(to_delete):
            loads.pop(idx)
        st.session_state.loads = loads

        if st.button("＋  Ajouter un appareil", use_container_width=True):
            st.session_state.loads.append({"name": "Nouvel appareil", "power": 0.0,
                                            "start_h": 8, "end_h": 20})
            st.rerun()

        # Totaux
        total_wh = sum(
            float(l["power"]) * (
                (l.get("end_h", 22) - l.get("start_h", 6))
                if l.get("end_h", 22) > l.get("start_h", 6)
                else (24 - l.get("start_h", 6) + l.get("end_h", 22))
            ) for l in loads
        )
        total_w = sum(float(l["power"]) for l in loads)
        st.divider()
        ct1, ct2 = st.columns(2)
        ct1.metric("⚡ Énergie journalière", f"{total_wh:.0f} Wh/j")
        ct2.metric("🔺 Puissance de pointe", f"{total_w:.0f} W")

    # ════════════════════════════════════════════════════════════════════════
    # 2.  PANNEAUX PV  +  CÂBLAGE
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("☀️  Panneaux photovoltaïques", expanded=True):

        # ── Technologie ───────────────────────────────────────────────────────
        col_tech, col_wire = st.columns(2)
        with col_tech:
            tech = st.selectbox(
                "🔬 Technologie",
                options=["Monocristallin", "Polycristallin"],
                index=["Monocristallin", "Polycristallin"].index(st.session_state.pv_technology),
                key="sel_pv_tech",
                help="Monocristallin : rendement 18–22 %. Polycristallin : rendement 15–18 %, moins cher.",
            )
            st.session_state.pv_technology = tech

        # ── Câblage ───────────────────────────────────────────────────────────
        with col_wire:
            wiring_opts   = {"parallel": "⚡ Parallèle  (I additive, V constante)",
                             "series":   "🔗 Série  (V additive, I constante)"}
            wiring_labels = list(wiring_opts.values())
            wiring_keys   = list(wiring_opts.keys())
            cur_idx = wiring_keys.index(st.session_state.pv_wiring)
            chosen  = st.selectbox(
                "🔌 Câblage des panneaux",
                options=wiring_labels,
                index=cur_idx,
                key="sel_wiring",
                help=(
                    "Parallèle : Voc champ = Voc panneau, Isc champ = Isc × N\n"
                    "Série     : Voc champ = Voc × N,     Isc champ = Isc panneau\n"
                    "Le régulateur est filtré automatiquement selon ce choix."
                ),
            )
            st.session_state.pv_wiring = wiring_keys[wiring_labels.index(chosen)]

        st.divider()

        # ── Modèle + nombre ───────────────────────────────────────────────────
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
            st.caption(f"Voc {panel['voc']} V · Isc {panel['isc']} A · "
                       f"Vmp {panel['vmp']} V · Imp {panel['imp']} A")

        with col2:
            st.session_state.pv_count = st.number_input(
                "Nombre de panneaux", min_value=1, max_value=50,
                value=st.session_state.pv_count, key="ni_pv_count",
            )
            panel   = PV_CATALOG[st.session_state.pv_model]
            peak_wc = panel["power"] * st.session_state.pv_count
            est_wh  = peak_wc * st.session_state.psh * PERFORMANCE_RATIO
            st.metric("Puissance crête", f"{peak_wc} Wc", delta=f"≈ {est_wh:.0f} Wh/j")

        # ── Résumé câblage en temps réel ──────────────────────────────────────
        panel   = PV_CATALOG[st.session_state.pv_model]
        wiring  = st.session_state.pv_wiring
        w       = calc_pv_wiring(panel, st.session_state.pv_count, wiring)
        wlabel  = "Parallèle" if wiring == "parallel" else "Série"

        st.markdown(
            f"<div style='background:rgba(123,158,212,0.07);border:1px solid rgba(123,158,212,0.18);"
            f"border-radius:8px;padding:10px 14px;font-size:12px;margin-top:8px;line-height:1.9;'>"
            f"<b>Champ {wlabel} ({st.session_state.pv_count} panneau(x))</b><br>"
            f"🔶 Voc champ : <b>{w['voc']:.1f} V</b> &nbsp;·&nbsp; "
            f"Isc champ : <b>{w['isc']:.2f} A</b><br>"
            f"🔷 Vmp champ : <b>{w['vmp']:.1f} V</b> &nbsp;·&nbsp; "
            f"Imp champ : <b>{w['imp']:.2f} A</b><br>"
            f"<span style='color:{TEXT2};font-size:11px;'>"
            + ("↳ I additive (parallèle) — régulateur min " + str(round(w['isc']*1.25,1)) + " A"
               if wiring == 'parallel'
               else "↳ V additive (série) — régulateur min " + str(round(w['voc'],1)) + " V") +
            "</span></div>",
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

    # ════════════════════════════════════════════════════════════════════════
    # 3.  BATTERIES
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🔋  Batteries", expanded=True):
        v        = st.session_state.system_voltage
        bat_opts = list(batteries_for_voltage(v).keys())
        _section_label(f"Batteries {v} V uniquement", TEXT2)

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.bat_model = st.selectbox(
                "Modèle", options=bat_opts,
                index=bat_opts.index(st.session_state.bat_model) if st.session_state.bat_model in bat_opts else 0,
                key="sel_bat_model",
            )
            bat = BATTERY_CATALOG[st.session_state.bat_model]
            st.caption(f"Techno : {bat['technology']} · DoD : {int(bat['dod']*100)}% · Cycles : {bat['cycles']}")

        with col2:
            st.session_state.bat_count = st.number_input(
                "Nombre", min_value=1, max_value=20,
                value=st.session_state.bat_count, key="ni_bat_count",
            )
            bat    = BATTERY_CATALOG[st.session_state.bat_model]
            usable = bat["capacity"] * st.session_state.bat_count * v * bat["dod"]
            total  = bat["capacity"] * st.session_state.bat_count * v
            st.metric("Capacité utile", f"{usable:.0f} Wh", delta=f"Totale : {total:.0f} Wh")

        st.session_state.autonomy_days = st.slider(
            "⏳ Autonomie souhaitée",
            min_value=1, max_value=7, value=st.session_state.autonomy_days,
            key="sl_auto", format="%d jour(s)",
            help="1 j = usage normal · 3 j+ = zone souvent nuageuse",
        )

        # Vérification capacité vs besoin
        loads     = st.session_state.loads
        total_wh_loads = sum(
            float(l["power"]) * (
                (l.get("end_h", 22) - l.get("start_h", 6))
                if l.get("end_h", 22) > l.get("start_h", 6)
                else (24 - l.get("start_h", 6) + l.get("end_h", 22))
            ) for l in loads
        )
        required    = total_wh_loads * st.session_state.autonomy_days
        bat_ok      = usable >= required
        s_color     = ACCENT if bat_ok else "#C0504A"
        st.markdown(
            f"<div style='font-size:12px;color:{s_color};margin-top:6px;'>"
            f"{'✓' if bat_ok else '⚠'} Requis : <b>{required:.0f} Wh</b> · "
            f"Disponible : <b>{usable:.0f} Wh</b> "
            f"{'→ OK' if bat_ok else '→ Insuffisant, augmentez le nombre de batteries'}"
            f"</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 4.  RÉGULATEUR  — filtré selon câblage PV réel
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("⚡  Régulateur de charge", expanded=True):
        panel  = PV_CATALOG[st.session_state.pv_model]
        wiring = st.session_state.pv_wiring
        w      = calc_pv_wiring(panel, st.session_state.pv_count, wiring)

        # Régulateurs filtrés selon le champ réel
        reg_all    = regulators_for_pv(w["isc"], w["voc"])
        reg_compat = {k: v for k, v in reg_all.items() if v["compatible"]}
        reg_incompat = {k: v for k, v in reg_all.items() if not v["compatible"]}

        wlabel = "Parallèle" if wiring == "parallel" else "Série"
        st.markdown(
            f"<div style='font-size:12px;color:{TEXT2};margin-bottom:10px;'>"
            f"Câblage <b>{wlabel}</b> → Isc champ = <b style='color:{ACCENT}'>{w['isc']:.2f} A</b>"
            f" · Voc champ = <b style='color:{ACCENT}'>{w['voc']:.1f} V</b><br>"
            f"Courant régulateur min requis : <b>{w['isc']*1.25:.1f} A</b> (Isc × 1.25)"
            f"</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if reg_compat:
                # Afficher d'abord les compatibles
                all_opts = list(reg_compat.keys()) + list(reg_incompat.keys())
                # Formater avec indicateur visuel
                def fmt_reg(k):
                    v = reg_all[k]
                    ok = "✅" if v["compatible"] else "⛔"
                    return f"{ok} {k}"

                cur = st.session_state.reg_model
                if cur not in all_opts:
                    cur = all_opts[0]
                    st.session_state.reg_model = cur

                chosen_fmt = st.selectbox(
                    "Modèle de régulateur",
                    options=[fmt_reg(k) for k in all_opts],
                    index=all_opts.index(cur),
                    key="sel_reg",
                    help="✅ = compatible avec votre câblage · ⛔ = sous-dimensionné",
                )
                # Récupérer la clé réelle depuis le label formaté
                chosen_key = all_opts[[fmt_reg(k) for k in all_opts].index(chosen_fmt)]
                st.session_state.reg_model = chosen_key
            else:
                st.error("⛔ Aucun régulateur compatible — vérifiez le nombre et le câblage des panneaux.")
                reg_keys = list(REGULATOR_CATALOG.keys())
                st.session_state.reg_model = st.selectbox(
                    "Modèle (aucun compatible)", options=reg_keys,
                    index=reg_keys.index(st.session_state.reg_model) if st.session_state.reg_model in reg_keys else 0,
                    key="sel_reg",
                )

        with col2:
            reg     = REGULATOR_CATALOG[st.session_state.reg_model]
            ok_i    = (w["isc"] * 1.25) <= reg["current_max"]
            ok_v    = w["voc"] <= reg["voltage_max"]
            ci      = ACCENT if ok_i else "#C0504A"
            cv_     = ACCENT if ok_v else "#C0504A"
            st.markdown(
                f"<div style='background:rgba(123,158,212,0.07);border-radius:8px;"
                f"padding:10px 12px;font-size:12px;line-height:1.9;'>"
                f"<b>{reg['type']}</b> · Rdt {int(reg['efficiency']*100)} %<br>"
                f"<span style='color:{ci};'>{'✓' if ok_i else '⚠'} Courant max : {reg['current_max']} A "
                f"(requis {w['isc']*1.25:.1f} A)</span><br>"
                f"<span style='color:{cv_};'>{'✓' if ok_v else '⚠'} Tension max : {reg['voltage_max']} V "
                f"(Voc champ {w['voc']:.1f} V)</span>"
                f"</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # 5.  ONDULEUR  — filtré par tension système + puissance de charge
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🔌  Onduleur", expanded=True):
        v        = st.session_state.system_voltage
        inv_opts = list(inverters_for_voltage(v).keys())
        peak_load = sum(float(l["power"]) for l in st.session_state.loads)

        _section_label(f"Onduleurs {v} V DC uniquement", TEXT2)
        st.markdown(
            f"<div style='font-size:12px;color:{TEXT2};margin-bottom:10px;'>"
            f"Puissance de charge totale : <b style='color:{ACCENT}'>{peak_load:.0f} W</b>"
            f"</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            def fmt_inv(k):
                inv = INVERTER_CATALOG[k]
                ok  = "✅" if peak_load <= inv["power"] else "⛔"
                return f"{ok} {k}"

            cur_inv = st.session_state.inv_model
            if cur_inv not in inv_opts:
                cur_inv = inv_opts[0]
                st.session_state.inv_model = cur_inv

            chosen_inv_fmt = st.selectbox(
                "Modèle d'onduleur",
                options=[fmt_inv(k) for k in inv_opts],
                index=inv_opts.index(cur_inv),
                key="sel_inv",
                help="✅ = suffisant pour votre charge · ⛔ = sous-dimensionné",
            )
            chosen_inv_key = inv_opts[[fmt_inv(k) for k in inv_opts].index(chosen_inv_fmt)]
            st.session_state.inv_model = chosen_inv_key

        with col2:
            inv     = INVERTER_CATALOG[st.session_state.inv_model]
            inv_ok  = peak_load <= inv["power"]
            ci      = ACCENT if inv_ok else "#C0504A"
            st.markdown(
                f"<div style='background:rgba(123,158,212,0.07);border-radius:8px;"
                f"padding:10px 12px;font-size:12px;line-height:1.9;'>"
                f"<b>{inv['power']} W</b> nominal · Crête {inv['power_peak']} W<br>"
                f"DC {inv['input_v']} V · Onde {inv['wave']} · Rdt {int(inv['efficiency']*100)} %<br>"
                f"<span style='color:{ci};font-weight:600;'>"
                f"{'✓ OK' if inv_ok else '⚠ Insuffisant'} — charge {peak_load:.0f} W"
                f"</span></div>", unsafe_allow_html=True)