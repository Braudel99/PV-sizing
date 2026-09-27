# reports.py — Génération des documents PDF (fiche technique + fiche client)
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from engines import total_load_power, total_load_daily_energy

ACCENT   = colors.HexColor("#1A4A96")
ACCENT_L = colors.HexColor("#EEF2FA")
TEXT2    = colors.HexColor("#6B7186")
OK_C     = colors.HexColor("#238B45")
ERR_C    = colors.HexColor("#C0504A")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1c", parent=ss["Heading1"], textColor=ACCENT, spaceAfter=6))
    ss.add(ParagraphStyle("H2c", parent=ss["Heading2"], textColor=ACCENT, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=9, textColor=TEXT2))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontSize=10, leading=14))
    return ss


def _clean(msg: str) -> str:
    """Retire le formatage markdown (**gras**) et les emojis des messages d'alerte pour le PDF."""
    return (msg.replace("**", "")
               .replace("⛔", "[!]").replace("⚠️", "[Attention]").replace("⚠", "[Attention]")
               .replace("✅", "[OK]").replace("ℹ️", "[Info]"))


def _table_style(header_bg=ACCENT, header_fg=colors.white):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR",  (0, 0), (-1, 0), header_fg),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#D4D7E3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ACCENT_L]),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])


# ═══════════════════════════════════════════════════════════════════════════
# FICHE TECHNIQUE — document complet pour l'installateur / le bureau d'études
# ═══════════════════════════════════════════════════════════════════════════
def generate_technical_pdf(results: dict, params: dict) -> bytes:
    ss  = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=1.6*cm, bottomMargin=1.6*cm,
                            leftMargin=1.8*cm, rightMargin=1.8*cm)
    story = []

    story.append(Paragraph("Fiche technique — Dimensionnement photovoltaïque", ss["H1c"]))
    story.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", ss["Small"]))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1, spaceAfter=8))

    # ── Paramètres système ────────────────────────────────────────────────────
    story.append(Paragraph("1. Paramètres système", ss["H2c"]))
    sys_data = [
        ["Tension du système", f"{params['system_voltage']} V"],
        ["Irradiation (PSH)", f"{params['psh']} h/j"],
        ["Autonomie batterie souhaitée", f"{params['autonomy_days']} jour(s)"],
        ["Technologie PV", params.get("pv_technology", "—")],
        ["Coefficient de performance (PR)", "0.75"],
    ]
    t = Table(sys_data, colWidths=[7*cm, 8*cm])
    t.setStyle(_table_style())
    story.append(t)

    # ── Charges ────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. Bilan des charges", ss["H2c"]))
    load_rows = [["Appareil", "P. unitaire (W)", "Qté", "Plage horaire", "Énergie (Wh/j)"]]
    for l in params["loads"]:
        qty = int(l.get("qty", 1))
        s, e = int(l.get("start_h", 6)), int(l.get("end_h", 22))
        dur = (e - s) if e > s else (24 - s + e) if e < s else 0
        wh  = float(l["power"]) * qty * dur
        load_rows.append([l["name"], f"{l['power']:.0f}", str(qty), f"{s:02d}h–{e:02d}h", f"{wh:.0f}"])
    load_rows.append(["TOTAL", "", "", "",
                      f"{total_load_daily_energy(params['loads']):.0f}"])
    t = Table(load_rows, colWidths=[5.2*cm, 3*cm, 1.5*cm, 3*cm, 3*cm])
    t.setStyle(_table_style())
    t.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                           ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DDE0EA"))]))
    story.append(t)
    story.append(Paragraph(
        f"Puissance de pointe : {total_load_power(params['loads']):.0f} W &nbsp;·&nbsp; "
        f"Énergie journalière : {total_load_daily_energy(params['loads']):.0f} Wh/j",
        ss["Small"]))

    # ── Champ photovoltaïque ────────────────────────────────────────────────────
    pv = results["pv"]
    wiring_lbl = "Série" if pv.get("wiring") == "series" else "Parallèle"
    story.append(Paragraph("3. Champ photovoltaïque", ss["H2c"]))
    pv_data = [
        ["Modèle de panneau", params.get("pv_model_name", "—")],
        ["Nombre de panneaux", str(pv.get("count", 0))],
        ["Montage", wiring_lbl],
        ["Puissance crête installée", f"{pv['peak_power']} Wc"],
        ["Production journalière estimée", f"{pv['daily_energy']:.0f} Wh/j"],
        ["Voc champ", f"{pv['voc']:.1f} V"],
        ["Isc champ", f"{pv['isc']:.2f} A"],
        ["Vmp champ", f"{pv['vmp']:.1f} V"],
        ["Imp champ", f"{pv['imp']:.2f} A"],
    ]
    t = Table(pv_data, colWidths=[7*cm, 8*cm])
    t.setStyle(_table_style())
    story.append(t)

    # ── Batterie ────────────────────────────────────────────────────────────────
    bat = results["battery"]
    story.append(Paragraph("4. Parc de batteries", ss["H2c"]))
    bat_data = [
        ["Modèle", bat.get("model", "—")],
        ["Nombre de batteries", str(bat.get("count", 0))],
        ["Capacité totale", f"{bat['total_ah']:.0f} Ah — {bat['total_wh']:.0f} Wh"],
        ["Capacité utile (DoD appliqué)", f"{bat['usable_wh']:.0f} Wh"],
        ["Autonomie réelle obtenue", f"{bat['autonomy']:.1f} jour(s)"],
        ["Statut", "Suffisant" if not bat["under_sized"] else "Insuffisant — revoir le dimensionnement"],
    ]
    t = Table(bat_data, colWidths=[7*cm, 8*cm])
    t.setStyle(_table_style())
    story.append(t)

    # ── Régulateur ────────────────────────────────────────────────────────────
    reg = results["regulator"]
    story.append(Paragraph("5. Régulateur de charge", ss["H2c"]))
    reg_data = [
        ["Modèle", reg.get("model", "—")],
        ["Rendement", f"{reg['efficiency']*100:.0f} %"],
        ["Courant requis (Isc × 1.25)", f"{reg['required_current']:.1f} A"],
        ["Tension requise (Voc champ)", f"{reg['required_voltage']:.1f} V"],
        ["Statut", "Compatible" if reg["compatible"] else "Non compatible — revoir le dimensionnement"],
    ]
    t = Table(reg_data, colWidths=[7*cm, 8*cm])
    t.setStyle(_table_style())
    story.append(t)

    # ── Onduleur ──────────────────────────────────────────────────────────────
    inv = results["inverter"]
    story.append(Paragraph("6. Onduleur", ss["H2c"]))
    inv_data = [
        ["Modèle", inv.get("model", "—")],
        ["Rendement", f"{inv['efficiency']*100:.0f} %"],
        ["Pertes énergétiques estimées", f"{inv['energy_loss']:.0f} Wh/j"],
        ["Statut", "Compatible" if inv["compatible"] else "Sous-dimensionné — revoir le dimensionnement"],
    ]
    t = Table(inv_data, colWidths=[7*cm, 8*cm])
    t.setStyle(_table_style())
    story.append(t)

    # ── Synthèse & alertes ────────────────────────────────────────────────────
    story.append(Paragraph("7. Synthèse", ss["H2c"]))
    story.append(Paragraph(f"Couverture solaire des besoins : <b>{results['coverage']:.0f} %</b>", ss["Body"]))
    story.append(Spacer(1, 4))
    color_hex = {"error": "#C0504A", "warning": "#B8860B", "info": "#6B7186", "success": "#238B45"}
    for level, msg in results["alerts"]:
        hexcol = color_hex.get(level, "#6B7186")
        story.append(Paragraph(f'<font color="{hexcol}">• {_clean(msg)}</font>', ss["Body"]))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D4D7E3"), thickness=0.5))
    story.append(Paragraph(
        "Document généré automatiquement par PV Sizing. Résultats indicatifs — "
        "à faire valider par un installateur certifié avant mise en œuvre.",
        ss["Small"]))

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
# FICHE DE DIMENSIONNEMENT — document simple à présenter au client
# ═══════════════════════════════════════════════════════════════════════════
def generate_client_pdf(results: dict, params: dict) -> bytes:
    ss  = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    story = []

    pv    = results["pv"]
    bat   = results["battery"]
    load  = results["load"]
    cov   = results["coverage"]
    wiring_lbl = "série" if pv.get("wiring") == "series" else "parallèle"

    story.append(Paragraph("Proposition de système solaire autonome", ss["H1c"]))
    story.append(Paragraph(f"Établi le {datetime.now().strftime('%d/%m/%Y')}", ss["Small"]))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1, spaceAfter=10))

    story.append(Paragraph(
        "Voici la configuration recommandée pour couvrir vos besoins électriques "
        "quotidiens à partir de l'énergie solaire.", ss["Body"]))
    story.append(Spacer(1, 10))

    # ── Chiffres clés ─────────────────────────────────────────────────────────
    key_data = [
        ["Votre consommation", f"{load['daily_energy']:.0f} Wh par jour"],
        ["Panneaux solaires", f"{pv.get('count', 0)} panneau(x) — {pv['peak_power']} Wc au total (montage {wiring_lbl})"],
        ["Batteries", f"{bat.get('count', 0)} batterie(s) — {bat['model'] if bat.get('model') else '—'}"],
        ["Autonomie sans soleil", f"{bat['autonomy']:.1f} jour(s)"],
        ["Couverture de vos besoins", f"{min(cov, 150):.0f} %"],
    ]
    t = Table(key_data, colWidths=[6*cm, 9.5*cm])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 14))

    # ── Équipement fourni ──────────────────────────────────────────────────────
    story.append(Paragraph("Équipement recommandé", ss["H2c"]))
    equip_data = [
        ["Composant", "Modèle", "Quantité"],
        ["Panneau solaire", params.get("pv_model_name", "—"), str(pv.get("count", 0))],
        ["Batterie", bat.get("model", "—"), str(bat.get("count", 0))],
        ["Régulateur de charge", results["regulator"].get("model", "—"), "1"],
        ["Onduleur", results["inverter"].get("model", "—"), "1"],
    ]
    t = Table(equip_data, colWidths=[5*cm, 7.5*cm, 3*cm])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 16))

    verdict = ("Ce système couvre confortablement vos besoins quotidiens."
               if cov >= 100 else
               "Ce système couvre une bonne partie de vos besoins ; un appoint "
               "occasionnel (groupe électrogène ou réseau) peut être nécessaire "
               "en période peu ensoleillée.")
    story.append(Paragraph(verdict, ss["Body"]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D4D7E3"), thickness=0.5))
    story.append(Paragraph(
        "Cette proposition est indicative et basée sur les informations fournies. "
        "Un installateur certifié doit valider le dimensionnement final avant "
        "l'installation.", ss["Small"]))

    doc.build(story)
    return buf.getvalue()