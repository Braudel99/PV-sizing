# engines.py — Moteurs de calcul du dimensionnement PV
import numpy as np
from data import PERFORMANCE_RATIO


# ── 1. Bilan de charge ───────────────────────────────────────────────────────
def calc_load(loads: list[dict]) -> dict:
    """
    Calcule la consommation journalière et le profil horaire.
    loads : liste de {"name", "power" (W), "hours" (h/j)}
    """
    daily_energy = sum(l["power"] * l["hours"] for l in loads)   # Wh/j
    peak_power   = sum(l["power"] for l in loads)                  # W

    # Profil horaire 24h — répartition uniforme entre 6h et 22h (16h d'activité)
    hourly_load = np.zeros(24)
    for h in range(6, 22):
        hourly_load[h] = daily_energy / 16.0

    return {
        "daily_energy":  daily_energy,   # Wh/j
        "peak_power":    peak_power,      # W
        "hourly_profile": hourly_load,    # Wh par heure
    }


# ── 2. Production PV ─────────────────────────────────────────────────────────
def calc_pv(panel: dict, count: int, psh: float) -> dict:
    """
    Calcule la production du champ PV.
    panel : dict du catalogue, count : nb panneaux, psh : heures de soleil pic
    """
    if not panel or count <= 0:
        return {"peak_power": 0, "daily_energy": 0, "current": 0, "hourly_profile": np.zeros(24)}

    peak_power   = panel["power"] * count                           # Wc
    daily_energy = peak_power * psh * PERFORMANCE_RATIO             # Wh/j
    current      = panel["imp"] * count                             # A

    # Profil horaire PV — courbe en cloche (6h→18h) normalisée
    hours = np.arange(24)
    # Cloche gaussienne centrée sur midi (12h), entre lever (6h) et coucher (18h)
    raw = np.exp(-0.5 * ((hours - 12.0) / 2.5) ** 2)
    raw[:6]  = 0.0
    raw[19:] = 0.0
    # Normaliser pour que la somme = daily_energy
    if raw.sum() > 0:
        hourly_pv = raw / raw.sum() * daily_energy
    else:
        hourly_pv = raw

    return {
        "peak_power":     peak_power,    # Wc
        "daily_energy":   daily_energy,  # Wh/j
        "current":        current,       # A
        "hourly_profile": hourly_pv,     # Wh par heure
    }


# ── 3. Batterie ──────────────────────────────────────────────────────────────
def calc_battery(battery: dict, count: int, system_voltage: int,
                 daily_energy: float, autonomy_days: int) -> dict:
    if not battery or count <= 0:
        return {"total_ah": 0, "total_wh": 0, "usable_wh": 0,
                "autonomy": 0, "under_sized": False}

    total_ah   = battery["capacity"] * count
    total_wh   = total_ah * system_voltage
    usable_wh  = total_wh * battery["dod"]
    autonomy   = usable_wh / daily_energy if daily_energy > 0 else 0
    required   = daily_energy * autonomy_days

    return {
        "total_ah":    total_ah,
        "total_wh":    total_wh,
        "usable_wh":   usable_wh,
        "autonomy":    autonomy,
        "required_wh": required,
        "under_sized": usable_wh < required,
    }


# ── 4. Régulateur ────────────────────────────────────────────────────────────
def calc_regulator(regulator: dict, pv_current: float, pv_voc: float) -> dict:
    if not regulator:
        return {"required_current": 0, "compatible": False,
                "current_ok": False, "voltage_ok": False, "efficiency": 0}

    required_current = pv_current * 1.25   # marge 25 %
    current_ok = required_current <= regulator["current_max"]
    voltage_ok = pv_voc           <= regulator["voltage_max"]

    return {
        "required_current": required_current,
        "compatible":       current_ok and voltage_ok,
        "current_ok":       current_ok,
        "voltage_ok":       voltage_ok,
        "efficiency":       regulator["efficiency"],
    }


# ── 5. Onduleur ──────────────────────────────────────────────────────────────
def calc_inverter(inverter: dict, peak_power: float, daily_energy: float) -> dict:
    if not inverter:
        return {"compatible": False, "under_sized": False,
                "over_sized": False, "efficiency": 0, "energy_loss": 0}

    under_sized = peak_power > inverter["power"]
    over_sized  = peak_power < inverter["power"] * 0.30
    energy_loss = daily_energy * (1 / inverter["efficiency"] - 1) if daily_energy > 0 else 0

    return {
        "compatible":   not under_sized,
        "under_sized":  under_sized,
        "over_sized":   over_sized,
        "efficiency":   inverter["efficiency"],
        "energy_loss":  energy_loss,
    }


# ── 6. Bilan complet + alertes ───────────────────────────────────────────────
def run_sizing(params: dict) -> dict:
    """
    Orchestre tous les moteurs et retourne un dict complet avec résultats + alertes.
    params : dict issu de st.session_state
    """
    panel     = params["panel"]
    battery   = params["battery"]
    regulator = params["regulator"]
    inverter  = params["inverter"]
    loads     = params["loads"]
    psh       = params["psh"]
    pv_count  = params["pv_count"]
    bat_count = params["bat_count"]
    sys_v     = params["system_voltage"]
    auto_days = params["autonomy_days"]

    load_r = calc_load(loads)
    pv_r   = calc_pv(panel, pv_count, psh)
    bat_r  = calc_battery(battery, bat_count, sys_v, load_r["daily_energy"], auto_days)
    reg_r  = calc_regulator(regulator, pv_r["current"], panel["voc"] * pv_count if panel else 0)
    inv_r  = calc_inverter(inverter, load_r["peak_power"], load_r["daily_energy"])

    coverage = (pv_r["daily_energy"] / load_r["daily_energy"] * 100
                if load_r["daily_energy"] > 0 else 0)

    # ── Alertes ──────────────────────────────────────────────────────────────
    alerts = []
    if bat_r["under_sized"]:
        alerts.append(("error",
            f"⛔ Batterie insuffisante — Utile : **{bat_r['usable_wh']:.0f} Wh**, "
            f"besoin : **{bat_r['required_wh']:.0f} Wh** ({auto_days} j d'autonomie)."))
    if not reg_r["current_ok"]:
        alerts.append(("error",
            f"⛔ Régulateur sous-dimensionné — Courant requis : **{reg_r['required_current']:.1f} A**, "
            f"max régulateur : **{regulator['current_max']} A**."))
    if not reg_r["voltage_ok"] and panel:
        alerts.append(("warning",
            f"⚠️ Tension PV (**{panel['voc'] * pv_count:.1f} V**) dépasse la limite du régulateur "
            f"(**{regulator['voltage_max']} V**)."))
    if inv_r["under_sized"]:
        alerts.append(("error",
            f"⛔ Onduleur sous-dimensionné — Charge : **{load_r['peak_power']} W**, "
            f"onduleur : **{inverter['power']} W**."))
    if inv_r["over_sized"]:
        alerts.append(("info",
            f"ℹ️ Onduleur sur-dimensionné — La charge représente moins de 30 % de sa capacité."))
    if coverage < 80:
        alerts.append(("warning",
            f"⚠️ Couverture solaire faible : **{coverage:.0f}%** — Ajoutez des panneaux ou réduisez la consommation."))
    if coverage > 110:
        alerts.append(("info",
            f"ℹ️ Production excédentaire : **{coverage:.0f}%** — Vous pouvez réduire le nombre de panneaux."))
    if not alerts:
        alerts.append(("success", "✅ Système correctement dimensionné — aucune anomalie détectée."))

    return {
        "load":      load_r,
        "pv":        pv_r,
        "battery":   bat_r,
        "regulator": reg_r,
        "inverter":  inv_r,
        "coverage":  coverage,
        "alerts":    alerts,
    }


# ── 7. Profil de charge batterie sur 24h ─────────────────────────────────────
def calc_battery_profile(pv_hourly: np.ndarray, load_hourly: np.ndarray,
                          usable_wh: float) -> dict:
    """
    Simule l'état de charge (SoC) de la batterie heure par heure.
    Retourne les profils pour le graphe 24h.
    """
    soc    = np.zeros(25)   # état de charge Wh (index 0 = 0h, index 24 = fin de journée)
    soc[0] = usable_wh      # batterie pleine en début de journée

    covered    = np.zeros(24)
    uncovered  = np.zeros(24)
    charge_bat = np.zeros(24)   # énergie stockée dans la batterie (>0)
    discharge  = np.zeros(24)   # énergie soutirée de la batterie (>0)

    for h in range(24):
        balance = pv_hourly[h] - load_hourly[h]

        if balance >= 0:
            # Surplus PV → charge batterie
            space = usable_wh - soc[h]
            stored = min(balance, space)
            charge_bat[h] = stored
            soc[h+1] = soc[h] + stored
            covered[h] = load_hourly[h]
        else:
            # Déficit → décharge batterie
            needed = -balance
            available = soc[h]
            drawn = min(needed, available)
            discharge[h] = drawn
            soc[h+1] = soc[h] - drawn
            covered[h]   = pv_hourly[h] + drawn
            uncovered[h] = max(0, load_hourly[h] - covered[h])

    return {
        "soc":        soc[:24],       # Wh
        "covered":    covered,        # Wh couverts par PV + batterie
        "uncovered":  uncovered,      # Wh non couverts
        "charge_bat": charge_bat,     # Wh stockés dans la batterie
        "discharge":  discharge,      # Wh soutirés de la batterie
    }
