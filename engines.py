# engines.py — Moteurs de calcul du dimensionnement PV  (v1.3)
import numpy as np
from data import PERFORMANCE_RATIO


# ── 1. Bilan de charge ───────────────────────────────────────────────────────
def calc_load(loads: list[dict]) -> dict:
    """
    Consommation journalière et profil horaire.
    Chaque charge a start_h / end_h pour sa plage d'activité.
    """
    hourly_load = np.zeros(24)

    for l in loads:
        power   = float(l.get("power", 0))
        start_h = int(l.get("start_h", 6))
        end_h   = int(l.get("end_h", 22))
        if power <= 0:
            continue

        if end_h > start_h:
            active_hours = list(range(start_h, end_h))
        elif end_h < start_h:          # passage minuit
            active_hours = list(range(start_h, 24)) + list(range(0, end_h))
        else:
            active_hours = []

        for h in active_hours:
            hourly_load[h] += power    # Wh par heure active

    daily_energy = float(np.sum(hourly_load))
    peak_power   = sum(float(l.get("power", 0)) for l in loads)

    return {
        "daily_energy":   daily_energy,
        "peak_power":     peak_power,
        "hourly_profile": hourly_load,
    }


# ── 2. Câblage du champ PV ───────────────────────────────────────────────────
def calc_pv_wiring(panel: dict, count: int, wiring: str) -> dict:
    """
    Calcule les grandeurs électriques du champ PV selon le câblage.

    Parallèle  (wiring="parallel") :
        Voc_champ  = Voc_panneau          tension identique
        Isc_champ  = Isc_panneau × N      courant multiplié
        Vmp_champ  = Vmp_panneau
        Imp_champ  = Imp_panneau × N

    Série      (wiring="series") :
        Voc_champ  = Voc_panneau × N      tension multipliée
        Isc_champ  = Isc_panneau          courant identique
        Vmp_champ  = Vmp_panneau × N
        Imp_champ  = Imp_panneau

    Retourne les valeurs du champ + la puissance crête (identique dans les deux cas).
    """
    if not panel or count <= 0:
        return {
            "peak_power": 0, "voc": 0, "isc": 0,
            "vmp": 0, "imp": 0, "wiring": wiring,
        }

    peak_power = panel["power"] * count   # Wc — identique série ou parallèle

    if wiring == "series":
        voc = panel["voc"] * count
        isc = panel["isc"]
        vmp = panel["vmp"] * count
        imp = panel["imp"]
    else:   # parallel (défaut)
        voc = panel["voc"]
        isc = panel["isc"] * count
        vmp = panel["vmp"]
        imp = panel["imp"] * count

    return {
        "peak_power": peak_power,
        "voc":        voc,    # tension circuit ouvert du champ (V)
        "isc":        isc,    # courant court-circuit du champ (A)
        "vmp":        vmp,    # tension au point de puissance max (V)
        "imp":        imp,    # courant au point de puissance max (A)
        "wiring":     wiring,
    }


# ── 3. Production PV ─────────────────────────────────────────────────────────
def calc_pv(panel: dict, count: int, psh: float, wiring: str = "parallel") -> dict:
    """
    Calcule la production énergétique + grandeurs électriques du champ.
    """
    if not panel or count <= 0:
        return {
            "peak_power": 0, "daily_energy": 0,
            "voc": 0, "isc": 0, "vmp": 0, "imp": 0,
            "wiring": wiring, "hourly_profile": np.zeros(24),
        }

    wiring_data  = calc_pv_wiring(panel, count, wiring)
    peak_power   = wiring_data["peak_power"]
    daily_energy = peak_power * psh * PERFORMANCE_RATIO

    # Profil horaire — cloche gaussienne centrée à 12h
    hours = np.arange(24)
    raw   = np.exp(-0.5 * ((hours - 12.0) / 2.5) ** 2)
    raw[:6]  = 0.0
    raw[19:] = 0.0
    hourly_pv = raw / raw.sum() * daily_energy if raw.sum() > 0 else raw

    return {
        "peak_power":     peak_power,
        "daily_energy":   daily_energy,
        "voc":            wiring_data["voc"],
        "isc":            wiring_data["isc"],
        "vmp":            wiring_data["vmp"],
        "imp":            wiring_data["imp"],
        "wiring":         wiring,
        "hourly_profile": hourly_pv,
    }


# ── 4. Batterie ──────────────────────────────────────────────────────────────
def calc_battery(battery: dict, count: int, system_voltage: int,
                 daily_energy: float, autonomy_days: int) -> dict:
    if not battery or count <= 0:
        return {"total_ah": 0, "total_wh": 0, "usable_wh": 0,
                "autonomy": 0, "under_sized": False, "required_wh": 0}

    total_ah  = battery["capacity"] * count
    total_wh  = total_ah * system_voltage
    usable_wh = total_wh * battery["dod"]
    autonomy  = usable_wh / daily_energy if daily_energy > 0 else 0
    required  = daily_energy * autonomy_days

    return {
        "total_ah":    total_ah,
        "total_wh":    total_wh,
        "usable_wh":   usable_wh,
        "autonomy":    autonomy,
        "required_wh": required,
        "under_sized": usable_wh < required,
    }


# ── 5. Régulateur ────────────────────────────────────────────────────────────
def calc_regulator(regulator: dict, pv_isc: float, pv_voc: float) -> dict:
    """
    Vérifie la compatibilité du régulateur avec le champ PV.

    Règle IEC / pratique terrain :
      - Courant requis = Isc_champ × 1.25  (marge de sécurité 25 %)
      - Tension entrée = Voc_champ          (tension circuit ouvert, worst case)

    En parallèle : Isc_champ grand, Voc_champ = Voc_panneau
    En série      : Isc_champ = Isc_panneau, Voc_champ grand
    """
    if not regulator:
        return {"required_current": 0, "compatible": False,
                "current_ok": False, "voltage_ok": False, "efficiency": 0}

    required_current = pv_isc * 1.25   # A avec marge 25 %
    current_ok = required_current <= regulator["current_max"]
    voltage_ok = pv_voc           <= regulator["voltage_max"]

    return {
        "required_current": required_current,
        "required_voltage":  pv_voc,
        "compatible":        current_ok and voltage_ok,
        "current_ok":        current_ok,
        "voltage_ok":        voltage_ok,
        "efficiency":        regulator["efficiency"],
    }


# ── 6. Onduleur ──────────────────────────────────────────────────────────────
def calc_inverter(inverter: dict, peak_power: float, daily_energy: float) -> dict:
    if not inverter:
        return {"compatible": False, "under_sized": False,
                "over_sized": False, "efficiency": 0, "energy_loss": 0}

    under_sized = peak_power > inverter["power"]
    over_sized  = peak_power < inverter["power"] * 0.30
    energy_loss = daily_energy * (1 / inverter["efficiency"] - 1) if daily_energy > 0 else 0

    return {
        "compatible":  not under_sized,
        "under_sized": under_sized,
        "over_sized":  over_sized,
        "efficiency":  inverter["efficiency"],
        "energy_loss": energy_loss,
    }


# ── 7. Orchestration complète ────────────────────────────────────────────────
def run_sizing(params: dict) -> dict:
    panel     = params["panel"]
    battery   = params["battery"]
    regulator = params["regulator"]
    inverter  = params["inverter"]
    loads     = params["loads"]
    psh       = params["psh"]
    pv_count  = params["pv_count"]
    pv_wiring = params.get("pv_wiring", "parallel")
    bat_count = params["bat_count"]
    sys_v     = params["system_voltage"]
    auto_days = params["autonomy_days"]

    load_r = calc_load(loads)
    pv_r   = calc_pv(panel, pv_count, psh, pv_wiring)
    bat_r  = calc_battery(battery, bat_count, sys_v, load_r["daily_energy"], auto_days)

    # Passage des bonnes grandeurs au régulateur selon câblage
    reg_r  = calc_regulator(regulator, pv_r["isc"], pv_r["voc"])
    inv_r  = calc_inverter(inverter, load_r["peak_power"], load_r["daily_energy"])

    coverage = (pv_r["daily_energy"] / load_r["daily_energy"] * 100
                if load_r["daily_energy"] > 0 else 0)

    # ── Alertes ──────────────────────────────────────────────────────────────
    wiring_label = "série" if pv_wiring == "series" else "parallèle"
    alerts = []

    if bat_r["under_sized"]:
        alerts.append(("error",
            f"⛔ Batterie insuffisante — Utile : **{bat_r['usable_wh']:.0f} Wh**, "
            f"besoin : **{bat_r['required_wh']:.0f} Wh** ({auto_days} j d'autonomie)."))

    if not reg_r["current_ok"]:
        alerts.append(("error",
            f"⛔ Régulateur sous-dimensionné en courant — "
            f"Isc champ ({pv_r['isc']:.1f} A) × 1.25 = **{reg_r['required_current']:.1f} A** requis, "
            f"max régulateur : **{regulator['current_max']} A**. "
            f"(Câblage {wiring_label} → courant {'élevé' if pv_wiring == 'parallel' else 'égal à Isc panneau'})"))

    if not reg_r["voltage_ok"] and panel:
        alerts.append(("error",
            f"⛔ Régulateur sous-dimensionné en tension — "
            f"Voc champ = **{pv_r['voc']:.1f} V**, "
            f"max régulateur : **{regulator['voltage_max']} V**. "
            f"(Câblage {wiring_label} → tension {'égale à Voc panneau' if pv_wiring == 'parallel' else 'élevée'})"))

    if inv_r["under_sized"]:
        alerts.append(("error",
            f"⛔ Onduleur sous-dimensionné — Charge : **{load_r['peak_power']} W**, "
            f"onduleur : **{inverter['power']} W**."))

    if inv_r["over_sized"]:
        alerts.append(("info",
            "ℹ️ Onduleur sur-dimensionné — charge < 30 % de la capacité nominale."))

    if coverage < 80:
        alerts.append(("warning",
            f"⚠️ Couverture solaire faible : **{coverage:.0f}%** — Ajoutez des panneaux."))

    if coverage > 110:
        alerts.append(("info",
            f"ℹ️ Production excédentaire : **{coverage:.0f}%** — Vous pouvez réduire les panneaux."))

    if not alerts:
        alerts.append(("success", "✅ Système correctement dimensionné."))

    return {
        "load":      load_r,
        "pv":        pv_r,
        "battery":   bat_r,
        "regulator": reg_r,
        "inverter":  inv_r,
        "coverage":  coverage,
        "alerts":    alerts,
    }


# ── 8. Profil SoC batterie sur 24h ───────────────────────────────────────────
def calc_battery_profile(pv_hourly: np.ndarray, load_hourly: np.ndarray,
                          usable_wh: float) -> dict:
    soc        = np.zeros(25)
    soc[0]     = usable_wh
    covered    = np.zeros(24)
    uncovered  = np.zeros(24)
    charge_bat = np.zeros(24)
    discharge  = np.zeros(24)

    for h in range(24):
        balance = pv_hourly[h] - load_hourly[h]
        if balance >= 0:
            stored        = min(balance, usable_wh - soc[h])
            charge_bat[h] = stored
            soc[h+1]      = soc[h] + stored
            covered[h]    = load_hourly[h]
        else:
            drawn         = min(-balance, soc[h])
            discharge[h]  = drawn
            soc[h+1]      = soc[h] - drawn
            covered[h]    = pv_hourly[h] + drawn
            uncovered[h]  = max(0, load_hourly[h] - covered[h])

    return {
        "soc":        soc[:24],
        "covered":    covered,
        "uncovered":  uncovered,
        "charge_bat": charge_bat,
        "discharge":  discharge,
    }