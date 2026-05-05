# dashboard.py — Tableau de bord : KPIs, alertes, graphes
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from engines import calc_battery_profile

# ── Palette graphes — sobre et lisible ───────────────────────────────────────
# Toutes les couleurs sont désaturées pour ne pas agresser l'œil
C_PV      = "#7EB8A4"   # vert sauge doux   — production PV
C_LOAD    = "#7A9FC2"   # bleu acier doux   — consommation
C_BAT_CH  = "#9DB87A"   # vert olive        — charge batterie
C_BAT_DC  = "#9E8FC2"   # mauve doux        — décharge batterie
C_SOC     = "#A8C4D4"   # bleu pâle         — état de charge
C_UNCOV   = "#C0504A"   # rouge brique mat  — zones non couvertes (intentionnellement plus vif pour alerter)


def render_alerts(alerts: list):
    for level, msg in alerts:
        if level == "error":
            st.error(msg)
        elif level == "warning":
            st.warning(msg)
        elif level == "success":
            st.success(msg)
        else:
            st.info(msg)


def render_kpis(results: dict, ACCENT: str = "#7B9ED4"):
    cov = results["coverage"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("☀️ Production PV",
              f"{results['pv']['daily_energy']:.0f} Wh/j",
              f"{results['pv']['peak_power']} Wc")
    c2.metric("⚡ Consommation",
              f"{results['load']['daily_energy']:.0f} Wh/j",
              f"Pointe {results['load']['peak_power']:.0f} W")
    c3.metric("🔋 Autonomie",
              f"{results['battery']['autonomy']:.1f} j",
              f"{results['battery']['usable_wh']:.0f} Wh utiles")
    c4.metric("📊 Couverture",
              f"{cov:.0f} %",
              "Suffisant" if cov >= 100 else ("Correct" if cov >= 80 else "Insuffisant"),
              delta_color="normal" if cov >= 80 else "inverse")


def render_energy_24h(results: dict, dark_mode: bool = True):
    """
    Graphe 24h principal.
    - Aire verte douce   : production PV
    - Aire bleue douce   : consommation
    - Zones rouges       : heures non couvertes (fond coloré + annotation)
    - Barres olive       : surplus stocké en batterie
    - Barres mauves      : décharge batterie
    - Ligne bleu pâle    : état de charge (axe droit)
    """
    pv_h   = results["pv"]["hourly_profile"]
    load_h = results["load"]["hourly_profile"]
    usable = results["battery"]["usable_wh"]

    bp    = calc_battery_profile(pv_h, load_h, usable)
    hours = list(range(24))

    grid_c  = "rgba(255,255,255,0.07)" if dark_mode else "rgba(0,0,0,0.06)"
    font_c  = "#7A8299" if dark_mode else "#6B7186"
    bg_c    = "rgba(0,0,0,0)"

    fig = go.Figure()

    # ── Zones non couvertes : fond rouge par plage horaire ───────────────────
    uncov = list(bp["uncovered"])
    uncov_hours = [h for h, v in enumerate(uncov) if v > 0]

    if uncov_hours:
        # Fond rouge transparent pour chaque heure non couverte
        for h in uncov_hours:
            fig.add_vrect(
                x0=h - 0.5, x1=h + 0.5,
                fillcolor="rgba(192, 80, 74, 0.18)",
                layer="below",
                line_width=0,
            )
        # Barre rouge pleine pour quantifier l'énergie manquante
        fig.add_trace(go.Bar(
            x=hours, y=uncov,
            name="⚠ Énergie non couverte",
            marker=dict(
                color=C_UNCOV,
                opacity=0.85,
                line=dict(color=C_UNCOV, width=0),
            ),
            hovertemplate="<b>%{y:.1f} Wh</b> non couverts<extra>%{x}h</extra>",
        ))

    # ── Décharge batterie ────────────────────────────────────────────────────
    discharge = list(bp["discharge"])
    if any(v > 0 for v in discharge):
        fig.add_trace(go.Bar(
            x=hours, y=discharge,
            name="Décharge batterie",
            marker=dict(color=C_BAT_DC, opacity=0.7),
            hovertemplate="%{y:.1f} Wh<extra>Décharge batterie</extra>",
        ))

    # ── Charge batterie ──────────────────────────────────────────────────────
    charge_b = list(bp["charge_bat"])
    if any(v > 0 for v in charge_b):
        fig.add_trace(go.Bar(
            x=hours, y=charge_b,
            name="Charge batterie",
            marker=dict(color=C_BAT_CH, opacity=0.7),
            hovertemplate="%{y:.1f} Wh<extra>Charge batterie</extra>",
        ))

    # ── Aire production PV ───────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=hours, y=list(pv_h),
        name="Production PV",
        fill="tozeroy",
        fillcolor="rgba(126,184,164,0.20)",
        line=dict(color=C_PV, width=2),
        mode="lines",
        hovertemplate="%{y:.1f} Wh<extra>Production PV</extra>",
    ))

    # ── Ligne consommation ───────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=hours, y=list(load_h),
        name="Consommation",
        fill="tozeroy",
        fillcolor="rgba(122,159,194,0.12)",
        line=dict(color=C_LOAD, width=2, dash="dot"),
        mode="lines",
        hovertemplate="%{y:.1f} Wh<extra>Consommation</extra>",
    ))

    # ── État de charge — axe secondaire ─────────────────────────────────────
    soc_pct = [v / usable * 100 if usable > 0 else 0 for v in bp["soc"]]
    fig.add_trace(go.Scatter(
        x=hours, y=soc_pct,
        name="État de charge (%)",
        line=dict(color=C_SOC, width=1.8, dash="dashdot"),
        mode="lines+markers",
        marker=dict(size=3.5, color=C_SOC),
        yaxis="y2",
        hovertemplate="%{y:.0f}%<extra>État de charge</extra>",
    ))

    # ── Annotation si aucune zone non couverte ───────────────────────────────
    annotations = []
    if not uncov_hours:
        annotations.append(dict(
            x=0.5, y=1.06, xref="paper", yref="paper",
            text="✓ Toutes les heures sont couvertes",
            showarrow=False,
            font=dict(size=11, color="#9DB87A"),
            xanchor="center",
        ))
    else:
        total_uncov = sum(uncov)
        annotations.append(dict(
            x=0.5, y=1.06, xref="paper", yref="paper",
            text=f"⚠ {len(uncov_hours)} heure(s) non couverte(s) — {total_uncov:.0f} Wh de déficit",
            showarrow=False,
            font=dict(size=11, color=C_UNCOV),
            xanchor="center",
        ))

    fig.update_layout(
        title=dict(
            text="Profil énergétique sur 24 heures",
            font=dict(size=14, color=font_c),
            x=0.5, xanchor="center", y=0.97,
        ),
        annotations=annotations,
        xaxis=dict(
            title="Heure",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}h" for h in range(0, 24, 2)],
            gridcolor=grid_c,
            color=font_c,
            range=[-0.5, 23.5],
        ),
        yaxis=dict(
            title="Énergie (Wh)",
            gridcolor=grid_c,
            color=font_c,
            zeroline=True,
            zerolinecolor=grid_c,
            rangemode="tozero",
        ),
        yaxis2=dict(
            title="SoC (%)",
            overlaying="y",
            side="right",
            range=[0, 115],
            showgrid=False,
            ticksuffix="%",
            color=font_c,
        ),
        barmode="overlay",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.09,
            xanchor="left", x=0,
            font=dict(size=10, color=font_c),
            bgcolor="rgba(0,0,0,0)",
        ),
        plot_bgcolor=bg_c,
        paper_bgcolor=bg_c,
        font=dict(color=font_c, size=11),
        margin=dict(t=100, b=48, l=58, r=64),
        height=440,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("ℹ️ Lire ce graphe"):
        st.markdown(
            "| Élément | Signification |\n"
            "|---|---|\n"
            "| **Fond rouge + barres rouges** | Heures non couvertes — ni PV ni batterie suffisants |\n"
            "| **Aire verte** | Production horaire PV (cloche centrée à midi) |\n"
            "| **Ligne bleue pointillée** | Consommation horaire des appareils (6h–22h) |\n"
            "| **Barres olive** | Surplus PV stocké dans la batterie |\n"
            "| **Barres mauves** | Énergie soutirée de la batterie pour compenser le déficit |\n"
            "| **Ligne bleue pâle** *(axe droit)* | État de charge batterie (0 = vide · 100 = pleine) |"
        )


def render_balance_bars(results: dict, dark_mode: bool = True):
    font_c = "#7A8299" if dark_mode else "#6B7186"
    grid_c = "rgba(255,255,255,0.07)" if dark_mode else "rgba(0,0,0,0.06)"

    labels = ["Production PV", "Consommation", "Stockage utile", "Pertes onduleur"]
    values = [
        results["pv"]["daily_energy"],
        results["load"]["daily_energy"],
        results["battery"]["usable_wh"],
        results["inverter"]["energy_loss"],
    ]
    colors = [C_PV, C_LOAD, C_BAT_CH, C_UNCOV]

    fig = go.Figure(go.Bar(
        x=values, y=labels,
        orientation="h",
        marker_color=colors,
        marker_opacity=0.85,
        text=[f"{v:.0f} Wh" for v in values],
        textposition="outside",
        textfont=dict(color=font_c, size=11),
        hovertemplate="%{x:.0f} Wh<extra>%{y}</extra>",
    ))
    fig.update_layout(
        title=dict(text="Bilan journalier", font=dict(size=13, color=font_c), x=0.5, xanchor="center"),
        xaxis=dict(title="Wh/j", gridcolor=grid_c, color=font_c),
        yaxis=dict(color=font_c),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_c, size=11),
        height=220,
        margin=dict(t=44, b=36, l=16, r=70),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_system_table(results: dict):
    r = results
    data = {
        "Composant": [
            "☀️ Panneaux PV", "⚙️ Régulateur",
            "🔋 Batterie", "🔌 Onduleur", "💡 Charges",
        ],
        "Valeur clé": [
            f"{r['pv']['peak_power']} Wc — {r['pv']['daily_energy']:.0f} Wh/j",
            f"Rdt {r['regulator']['efficiency']*100:.0f}% — Courant requis {r['regulator']['required_current']:.1f} A",
            f"{r['battery']['total_ah']:.0f} Ah — {r['battery']['usable_wh']:.0f} Wh utiles — {r['battery']['autonomy']:.1f} j",
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
        unsafe_allow_html=True
    )

    render_alerts(results["alerts"])
    st.divider()

    st.markdown(f"<p style='font-size:11px; font-weight:600; color:{TEXT2}; letter-spacing:0.06em; margin-bottom:8px;'>INDICATEURS CLÉS</p>", unsafe_allow_html=True)
    render_kpis(results, ACCENT=ACCENT)
    st.divider()

    st.markdown(f"<p style='font-size:11px; font-weight:600; color:{TEXT2}; letter-spacing:0.06em; margin-bottom:4px;'>PROFIL ÉNERGÉTIQUE 24H</p>", unsafe_allow_html=True)
    render_energy_24h(results, dark_mode=dark_mode)
    st.divider()

    st.markdown(f"<p style='font-size:11px; font-weight:600; color:{TEXT2}; letter-spacing:0.06em; margin-bottom:4px;'>BILAN JOURNALIER</p>", unsafe_allow_html=True)
    render_balance_bars(results, dark_mode=dark_mode)
    st.divider()

    st.markdown(f"<p style='font-size:11px; font-weight:600; color:{TEXT2}; letter-spacing:0.06em; margin-bottom:8px;'>ÉTAT DES COMPOSANTS</p>", unsafe_allow_html=True)
    render_system_table(results)