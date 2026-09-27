# engines.py — Moteurs de calcul du dimensionnement PV  (v1.5)
import math
import numpy as np
from data import (
    PERFORMANCE_RATIO, REGULATOR_CATALOG,
    batteries_for_voltage, inverters_for_voltage, regulators_for_pv,
)


# ── 1. Bilan de charge ───────────────────────────────────────────────────────
def calc_load(loads: list[dict]) -> dict:
    """
    Consommation journalière et profil horaire.
    Chaque charge a une quantité (qty), une puissance unitaire (power)
    et start_h / end_h pour sa plage d'activité.
    """
    hourly_load = np.zeros(24)

    for l in loads:
        qty     = int(l.get("qty", 1))
        power   = float(l.get("power", 0)) * qty
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
    peak_power   = total_load_power(loads)

    return {
        "daily_energy":   daily_energy,
        "peak_power":     peak_power,
        "hourly_profile": hourly_load,
    }


def total_load_power(loads: list[dict]) -> float:
    """Puissance de pointe totale (W), quantité comprise."""
    return sum(float(l.get("power", 0)) * int(l.get("qty", 1)) for l in loads)


def total_load_daily_energy(loads: list[dict]) -> float:
    """Énergie journalière totale (Wh/j), quantité comprise."""
    total = 0.0
    for l in loads:
        qty     = int(l.get("qty", 1))
        power   = float(l.get("power", 0)) * qty
        start_h = int(l.get("start_h", 6))
        end_h   = int(l.get("end_h", 22))
        if end_h > start_h:
            dur = end_h - start_h
        elif end_h < start_h:
            dur = 24 - start_h + end_h
        else:
            dur = 0
        total += power * dur
    return total


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


# ── 7a. Dimensionnement automatique du champ PV ──────────────────────────────
def size_pv_count(daily_energy_required: float, panel: dict, psh: float) -> int:
    """
    Nombre de panneaux nécessaires pour couvrir le besoin énergétique journalier,
    compte tenu de l'irradiation (PSH) et du coefficient de performance.
    """
    if not panel or psh <= 0 or daily_energy_required <= 0:
        return 1
    per_panel_daily = panel["power"] * psh * PERFORMANCE_RATIO
    if per_panel_daily <= 0:
        return 1
    return max(1, math.ceil(daily_energy_required / per_panel_daily))


# ── 7b. Sélection automatique du parc batteries ──────────────────────────────
def size_battery_count(daily_energy: float, autonomy_days: int,
                        battery: dict, system_voltage: int) -> int:
    """
    Nombre de batteries nécessaires pour couvrir l'autonomie souhaitée.
    """
    if not battery or daily_energy <= 0:
        return 1
    required_wh        = daily_energy * autonomy_days
    usable_per_battery  = battery["capacity"] * system_voltage * battery["dod"]
    if usable_per_battery <= 0:
        return 1
    return max(1, math.ceil(required_wh / usable_per_battery))


def choose_battery_bank(daily_energy: float, autonomy_days: int, system_voltage: int):
    """
    Choisit automatiquement, parmi les modèles compatibles avec la tension système,
    celui qui minimise le nombre de batteries nécessaires (meilleure capacité utile).
    Retourne (clé_modèle, dict_modèle, nombre).
    """
    candidates = batteries_for_voltage(system_voltage)
    if not candidates:
        return None, None, 0

    best_key, best_bat, best_count = None, None, None
    for key, bat in candidates.items():
        count = size_battery_count(daily_energy, autonomy_days, bat, system_voltage)
        if best_count is None or count < best_count:
            best_key, best_bat, best_count = key, bat, count

    return best_key, best_bat, best_count


# ── 7c. Choix automatique du montage PV + régulateur ─────────────────────────
def choose_regulator_and_wiring(panel: dict, count: int):
    """
    Choisit automatiquement le montage (série/parallèle) et le régulateur le plus
    économique (calibre le plus proche du besoin) compatible avec le champ PV.
    Parallèle est privilégié par défaut ; bascule en série si nécessaire.
    Retourne (wiring, clé_régulateur, dict_régulateur).
    """
    if not panel or count <= 0:
        fallback_key = min(REGULATOR_CATALOG, key=lambda k: REGULATOR_CATALOG[k]["current_max"])
        return "parallel", fallback_key, REGULATOR_CATALOG[fallback_key]

    for wiring in ("parallel", "series"):
        w      = calc_pv_wiring(panel, count, wiring)
        regs   = regulators_for_pv(w["isc"], w["voc"])
        compat = {k: v for k, v in regs.items() if v["compatible"]}
        if compat:
            key = min(compat, key=lambda k: (compat[k]["current_max"], compat[k]["voltage_max"]))
            return wiring, key, REGULATOR_CATALOG[key]

    # Aucun régulateur compatible : on retient le plus gros calibre disponible
    # (l'insuffisance sera signalée par les alertes du régulateur).
    fallback_key = max(REGULATOR_CATALOG,
                       key=lambda k: (REGULATOR_CATALOG[k]["current_max"], REGULATOR_CATALOG[k]["voltage_max"]))
    return "parallel", fallback_key, REGULATOR_CATALOG[fallback_key]


# ── 7d. Choix automatique de l'onduleur ──────────────────────────────────────
def choose_inverter(peak_load: float, system_voltage: int):
    """
    Choisit automatiquement, parmi les onduleurs compatibles avec la tension
    système, le plus petit modèle suffisant pour la puissance de pointe.
    Retourne (clé_modèle, dict_modèle).
    """
    candidates = inverters_for_voltage(system_voltage)
    if not candidates:
        return None, None

    compat = {k: v for k, v in candidates.items() if v["power"] >= peak_load}
    if compat:
        key = min(compat, key=lambda k: compat[k]["power"])
    else:
        # Aucun modèle suffisant : on retient le plus puissant disponible
        # (l'insuffisance sera signalée par les alertes de l'onduleur).
        key = max(candidates, key=lambda k: candidates[k]["power"])

    return key, candidates[key]


# ── 8. Orchestration complète ─────────────────────────────────────────────────
def run_sizing(params: dict) -> dict:
    panel     = params["panel"]
    loads     = params["loads"]
    psh       = params["psh"]
    sys_v     = params["system_voltage"]
    auto_days = params["autonomy_days"]

    load_r = calc_load(loads)

    # ── Dimensionnement + sélection automatique de tous les composants ────────
    pv_count             = size_pv_count(load_r["daily_energy"], panel, psh)
    pv_wiring, reg_key, regulator = choose_regulator_and_wiring(panel, pv_count)
    pv_r                 = calc_pv(panel, pv_count, psh, pv_wiring)
    pv_r["count"]        = pv_count

    bat_key, battery, bat_count = choose_battery_bank(load_r["daily_energy"], auto_days, sys_v)
    bat_r          = calc_battery(battery, bat_count, sys_v, load_r["daily_energy"], auto_days)
    bat_r["count"] = bat_count
    bat_r["model"] = bat_key

    inv_key, inverter = choose_inverter(load_r["peak_power"], sys_v)

    # Passage des bonnes grandeurs au régulateur selon câblage
    reg_r  = calc_regulator(regulator, pv_r["isc"], pv_r["voc"])
    reg_r["model"] = reg_key
    inv_r  = calc_inverter(inverter, load_r["peak_power"], load_r["daily_energy"])
    inv_r["model"] = inv_key

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