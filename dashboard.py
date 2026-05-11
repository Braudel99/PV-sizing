# dashboard.py — Tableau de bord  (v1.2)
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from engines import calc_battery_profile

# Palette graphes — cohérente et sobre
C_PV     = "#6BAED6"   # bleu ciel      — production PV
C_LOAD   = "#FD8D3C"   # orange doux    — consommation
C_BAT_CH = "#74C476"   # vert doux      — charge batterie
C_BAT_DC = "#9E9AC8"   # mauve doux     — décharge batterie
C_SOC    = "#41B6C4"   # cyan           — état de charge
C_UNCOV  = "#CB181D"   # rouge vif      — non couvert (intentionnel)
C_COVER  = "#238B45"   # vert foncé     — couvert


def render_alerts(alerts: list):
    for level, msg in alerts:
        if level == "error":   st.error(msg)
        elif level == "warning": st.warning(msg)
        elif level == "success": st.success(msg)
        else:                    st.info(msg)


def render_kpis(results: dict, ACCENT: str = "#7B9ED4", TEXT2: str = "#7A8299"):
    cov = results["coverage"]
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "☀️ Production PV",
        f"{results['pv']['daily_energy']:.0f} Wh/j",
        f"{results['pv']['peak_power']} Wc installés",
    )
    c2.metric(
        "⚡ Consommation",
        f"{results['load']['daily_energy']:.0f} Wh/j",
        f"Pointe {results['load']['peak_power']:.0f} W",
    )
    c3.metric(
        "🔋 Autonomie réelle",
        f"{results['battery']['autonomy']:.1f} j",
        f"{results['battery']['usable_wh']:.0f} Wh utiles",
    )
    # Couverture avec couleur dynamique via delta_color
    cov_label = "✓ Suffisant" if cov >= 100 else ("~ Correct" if cov >= 80 else "✗ Insuffisant")
    c4.metric(
        "📊 Couverture solaire",
        f"{min(cov, 150):.0f} %",
        cov_label,
        delta_color="normal" if cov >= 80 else "inverse",
    )


def render_coverage_gauge(coverage: float, dark_mode: bool, TEXT2: str):
    """Jauge circulaire du taux de couverture."""
    cov_clamped = min(coverage, 150)
    if coverage >= 100:
        bar_color, title_color = C_BAT_CH, C_BAT_CH
    elif coverage >= 80:
        bar_color, title_color = "#FD8D3C", "#FD8D3C"
    else:
        bar_color, title_color = C_UNCOV, C_UNCOV

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=cov_clamped,
        number={"suffix": "%", "font": {"size": 28, "color": title_color, "family": "IBM Plex Mono"}},
        delta={"reference": 100, "suffix": "%",
               "increasing": {"color": C_BAT_CH}, "decreasing": {"color": C_UNCOV}},
        gauge={
            "axis": {"range": [0, 150], "tickwidth": 1, "tickcolor": TEXT2,
                     "tickvals": [0, 50, 80, 100, 120, 150],
                     "ticktext": ["0%","50%","80%","100%","120%","150%"]},
            "bar":  {"color": bar_color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 80],   "color": "rgba(203,24,29,0.12)"},
                {"range": [80, 100], "color": "rgba(253,141,60,0.12)"},
                {"range": [100,150], "color": "rgba(116,196,118,0.12)"},
            ],
            "threshold": {"line": {"color": TEXT2, "width": 2}, "thickness": 0.75, "value": 100},
        },
        title={"text": "Couverture solaire", "font": {"size": 12, "color": TEXT2}},
    ))
    fig.update_layout(
        height=200,
        margin=dict(t=40, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT2),
    )
    return fig


def render_energy_24h(results: dict, dark_mode: bool = True):
    """Graphe 24h avec zones non couvertes clairement marquées en rouge."""
    pv_h   = results["pv"]["hourly_profile"]
    load_h = results["load"]["hourly_profile"]
    usable = results["battery"]["usable_wh"]

    bp    = calc_battery_profile(pv_h, load_h, usable)
    hours = list(range(24))

    grid_c = "rgba(255,255,255,0.07)" if dark_mode else "rgba(0,0,0,0.06)"
    font_c = "#7A8299" if dark_mode else "#6B7186"

    fig = go.Figure()

    # ── Fond rouge sur les heures non couvertes ──────────────────────────────
    uncov       = list(bp["uncovered"])
    uncov_hours = [h for h, v in enumerate(uncov) if v > 0]
    for h in uncov_hours:
        fig.add_vrect(x0=h - 0.5, x1=h + 0.5,
                      fillcolor="rgba(203,24,29,0.14)", layer="below", line_width=0)

    # ── Barres empilées dans cet ordre : non couvert / décharge / charge bat ──
    if any(v > 0 for v in uncov):
        fig.add_trace(go.Bar(
            x=hours, y=uncov, name="⛔ Non couvert",
            marker=dict(color=C_UNCOV, opacity=0.9),
            hovertemplate="<b>%{y:.1f} Wh</b> manquants<extra>%{x}h</extra>",
        ))

    discharge = list(bp["discharge"])
    if any(v > 0 for v in discharge):
        fig.add_trace(go.Bar(
            x=hours, y=discharge, name="Décharge batterie",
            marker=dict(color=C_BAT_DC, opacity=0.75),
            hovertemplate="%{y:.1f} Wh déchargés<extra>%{x}h</extra>",
        ))

    charge_b = list(bp["charge_bat"])
    if any(v > 0 for v in charge_b):
        fig.add_trace(go.Bar(
            x=hours, y=charge_b, name="Charge batterie",
            marker=dict(color=C_BAT_CH, opacity=0.75),
            hovertemplate="%{y:.1f} Wh stockés<extra>%{x}h</extra>",
        ))

    # ── Courbe PV ─────────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=hours, y=list(pv_h), name="Production PV",
        fill="tozeroy", fillcolor="rgba(107,174,214,0.18)",
        line=dict(color=C_PV, width=2.5),
        mode="lines",
        hovertemplate="%{y:.1f} Wh<extra>Production PV</extra>",
    ))

    # ── Courbe consommation ───────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=hours, y=list(load_h), name="Consommation",
        fill="tozeroy", fillcolor="rgba(253,141,60,0.10)",
        line=dict(color=C_LOAD, width=2.5, dash="dot"),
        mode="lines",
        hovertemplate="%{y:.1f} Wh<extra>Consommation</extra>",
    ))

    # ── État de charge — axe secondaire ──────────────────────────────────────
    soc_pct = [v / usable * 100 if usable > 0 else 0 for v in bp["soc"]]
    fig.add_trace(go.Scatter(
        x=hours, y=soc_pct, name="SoC batterie (%)",
        line=dict(color=C_SOC, width=2, dash="dashdot"),
        mode="lines+markers", marker=dict(size=3.5, color=C_SOC),
        yaxis="y2",
        hovertemplate="%{y:.0f}%<extra>SoC batterie</extra>",
    ))

    # ── Annotation résumé ─────────────────────────────────────────────────────
    if uncov_hours:
        txt = f"⛔ {len(uncov_hours)} h non couvertes · déficit {sum(uncov):.0f} Wh"
        col = C_UNCOV
    else:
        txt = "✓ Toutes les heures sont couvertes"
        col = C_BAT_CH

    fig.update_layout(
        annotations=[dict(
            x=0.5, y=1.07, xref="paper", yref="paper",
            text=txt, showarrow=False,
            font=dict(size=12, color=col), xanchor="center",
        )],
        title=dict(text="Profil énergétique sur 24 heures",
                   font=dict(size=14, color=font_c), x=0.5, y=0.97),
        xaxis=dict(
            title="Heure", tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}h" for h in range(0, 24, 2)],
            gridcolor=grid_c, color=font_c, range=[-0.5, 23.5],
        ),
        yaxis=dict(title="Énergie (Wh)", gridcolor=grid_c, color=font_c,
                   zeroline=True, zerolinecolor=grid_c, rangemode="tozero"),
        yaxis2=dict(title="SoC (%)", overlaying="y", side="right",
                    range=[0, 115], showgrid=False, ticksuffix="%", color=font_c),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="left", x=0,
                    font=dict(size=10, color=font_c), bgcolor="rgba(0,0,0,0)"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_c, size=11),
        margin=dict(t=105, b=48, l=58, r=64),
        height=450,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("ℹ️ Lire ce graphe"):
        st.markdown(
            "| Élément | Signification |\n|---|---|\n"
            "| 🔴 **Fond rouge + barres rouges** | Heures non couvertes — ni PV ni batterie disponible |\n"
            "| 🔵 **Aire bleue** | Production horaire PV (courbe en cloche, pic à midi) |\n"
            "| 🟠 **Ligne orange pointillée** | Consommation horaire des appareils |\n"
            "| 🟢 **Barres vertes** | Surplus PV stocké dans la batterie |\n"
            "| 🟣 **Barres mauves** | Énergie soutirée de la batterie pour compenser le déficit |\n"
            "| 🩵 **Ligne cyan** *(axe droit)* | État de charge batterie (0 % = vide · 100 % = pleine) |"
        )


def render_balance_bars(results: dict, dark_mode: bool = True):
    font_c = "#7A8299" if dark_mode else "#6B7186"
    grid_c = "rgba(255,255,255,0.07)" if dark_mode else "rgba(0,0,0,0.06)"

    # Graphe côte à côte : production vs consommation + stockage
    labels = ["Production PV", "Consommation", "Stockage utile", "Pertes onduleur"]
    values = [
        results["pv"]["daily_energy"],
        results["load"]["daily_energy"],
        results["battery"]["usable_wh"],
        results["inverter"]["energy_loss"],
    ]
    colors = [C_PV, C_LOAD, C_BAT_CH, C_UNCOV]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors, marker_opacity=0.85,
        text=[f"{v:.0f} Wh" for v in values],
        textposition="outside",
        textfont=dict(color=font_c, size=11),
        hovertemplate="%{x:.0f} Wh<extra>%{y}</extra>",
    ))
    fig.update_layout(
        title=dict(text="Bilan énergétique journalier",
                   font=dict(size=13, color=font_c), x=0.5, xanchor="center"),
        xaxis=dict(title="Wh/j", gridcolor=grid_c, color=font_c),
        yaxis=dict(color=font_c),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_c, size=11),
        height=220, margin=dict(t=44, b=36, l=16, r=80),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_system_table(results: dict, ACCENT: str = "#7B9ED4"):
    r = results
    data = {
        "Composant": ["☀️ Panneaux PV", "⚙️ Régulateur", "🔋 Batterie", "🔌 Onduleur", "💡 Charges"],
        "Valeur clé": [
            f"{r['pv']['peak_power']} Wc — {r['pv']['daily_energy']:.0f} Wh/j",
            f"Rdt {r['regulator']['efficiency']*100:.0f}% — Courant requis {r['regulator']['required_current']:.1f} A",
            f"{r['battery']['total_ah']:.0f} Ah — {r['battery']['usable_wh']:.0f} Wh utiles — {r['battery']['autonomy']:.1f} j autonomie",
            f"Rdt {r['inverter']['efficiency']*100:.0f}% — Pertes {r['inverter']['energy_loss']:.0f} Wh/j",
            f"{r['load']['peak_power']:.0f} W pointe — {r['load']['daily_energy']:.0f} Wh/j",
        ],
        "Statut": [
            "✅ OK",
            "✅ OK" if r["regulator"]["compatible"] else "⛔ Problème",
            "✅ OK" if not r["battery"]["under_sized"] else "⛔ Insuffisant",
            "✅ OK" if r["inverter"]["compatible"]  else "⛔ Sous-dim.",
            "✅ OK",
        ],
    }
    st.dataframe(data, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard(results: dict, params: dict, dark_mode: bool = True,
                     TEXT="#CDD1DC", TEXT2="#7A8299", ACCENT="#7B9ED4",
                     CARD="#1F2433", BORDER="#2C3245"):

    st.markdown(
        "<h2 style='text-align:center; font-size:20px; margin-bottom:18px;'>📊 Résultats de la simulation</h2>",
        unsafe_allow_html=True,
    )

    # ── Alertes ───────────────────────────────────────────────────────────────
    render_alerts(results["alerts"])
    st.divider()

    # ── KPIs + Jauge couverture ────────────────────────────────────────────────
    st.markdown(f"<p style='font-size:10px;font-weight:700;letter-spacing:0.08em;color:{TEXT2};text-transform:uppercase;margin-bottom:10px;'>INDICATEURS CLÉS</p>",
                unsafe_allow_html=True)

    col_kpis, col_gauge = st.columns([3, 1.2])
    with col_kpis:
        render_kpis(results, ACCENT=ACCENT, TEXT2=TEXT2)
    with col_gauge:
        fig_gauge = render_coverage_gauge(results["coverage"], dark_mode, TEXT2)
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # ── Graphe 24h ────────────────────────────────────────────────────────────
    st.markdown(f"<p style='font-size:10px;font-weight:700;letter-spacing:0.08em;color:{TEXT2};text-transform:uppercase;margin-bottom:4px;'>PROFIL ÉNERGÉTIQUE 24H</p>",
                unsafe_allow_html=True)
    render_energy_24h(results, dark_mode=dark_mode)
    st.divider()

    # ── Bilan barres + tableau côte à côte ───────────────────────────────────
    col_bal, col_tbl = st.columns([1.4, 1])

    with col_bal:
        st.markdown(f"<p style='font-size:10px;font-weight:700;letter-spacing:0.08em;color:{TEXT2};text-transform:uppercase;margin-bottom:4px;'>BILAN JOURNALIER</p>",
                    unsafe_allow_html=True)
        render_balance_bars(results, dark_mode=dark_mode)

    with col_tbl:
        st.markdown(f"<p style='font-size:10px;font-weight:700;letter-spacing:0.08em;color:{TEXT2};text-transform:uppercase;margin-bottom:8px;'>ÉTAT DES COMPOSANTS</p>",
                    unsafe_allow_html=True)
        render_system_table(results, ACCENT=ACCENT)