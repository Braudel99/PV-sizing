# data.py — Catalogues de matériels et constantes physiques  (v1.3)

PERFORMANCE_RATIO = 0.75
PSH_DEFAULT       = 5.0

# ── Panneaux PV ──────────────────────────────────────────────────────────────
PV_CATALOG = {
    "Mono 50 Wc":  {"power": 50,  "voc": 21.6, "isc": 3.11, "vmp": 17.6, "imp": 2.84, "technology": "Monocristallin"},
    "Mono 100 Wc": {"power": 100, "voc": 22.5, "isc": 5.96, "vmp": 18.2, "imp": 5.49, "technology": "Monocristallin"},
    "Mono 150 Wc": {"power": 150, "voc": 23.1, "isc": 8.70, "vmp": 18.9, "imp": 7.94, "technology": "Monocristallin"},
    "Mono 200 Wc": {"power": 200, "voc": 24.3, "isc": 10.98,"vmp": 20.1, "imp": 9.95, "technology": "Monocristallin"},
    "Mono 300 Wc": {"power": 300, "voc": 45.2, "isc": 9.01, "vmp": 37.8, "imp": 7.94, "technology": "Monocristallin"},
    "Poly 50 Wc":  {"power": 50,  "voc": 21.2, "isc": 3.05, "vmp": 17.2, "imp": 2.75, "technology": "Polycristallin"},
    "Poly 100 Wc": {"power": 100, "voc": 22.0, "isc": 5.80, "vmp": 17.8, "imp": 5.30, "technology": "Polycristallin"},
    "Poly 150 Wc": {"power": 150, "voc": 22.8, "isc": 8.45, "vmp": 18.5, "imp": 7.70, "technology": "Polycristallin"},
    "Poly 200 Wc": {"power": 200, "voc": 23.8, "isc": 10.60,"vmp": 19.6, "imp": 9.60, "technology": "Polycristallin"},
    "Poly 300 Wc": {"power": 300, "voc": 44.5, "isc": 8.80, "vmp": 37.0, "imp": 7.70, "technology": "Polycristallin"},
}

# ── Batteries ────────────────────────────────────────────────────────────────
BATTERY_CATALOG = {
    "12V —  50 Ah AGM":     {"capacity": 50,  "voltage": 12, "technology": "AGM",     "dod": 0.50, "cycles": 500},
    "12V — 100 Ah AGM":     {"capacity": 100, "voltage": 12, "technology": "AGM",     "dod": 0.50, "cycles": 600},
    "12V — 150 Ah GEL":     {"capacity": 150, "voltage": 12, "technology": "GEL",     "dod": 0.60, "cycles": 800},
    "12V — 200 Ah Lithium": {"capacity": 200, "voltage": 12, "technology": "Lithium", "dod": 0.80, "cycles": 2000},
    "24V —  50 Ah AGM":     {"capacity": 50,  "voltage": 24, "technology": "AGM",     "dod": 0.50, "cycles": 500},
    "24V — 100 Ah AGM":     {"capacity": 100, "voltage": 24, "technology": "AGM",     "dod": 0.50, "cycles": 600},
    "24V — 150 Ah GEL":     {"capacity": 150, "voltage": 24, "technology": "GEL",     "dod": 0.60, "cycles": 800},
    "24V — 200 Ah Lithium": {"capacity": 200, "voltage": 24, "technology": "Lithium", "dod": 0.80, "cycles": 2000},
    "48V —  50 Ah AGM":     {"capacity": 50,  "voltage": 48, "technology": "AGM",     "dod": 0.50, "cycles": 500},
    "48V — 100 Ah AGM":     {"capacity": 100, "voltage": 48, "technology": "AGM",     "dod": 0.50, "cycles": 600},
    "48V — 150 Ah GEL":     {"capacity": 150, "voltage": 48, "technology": "GEL",     "dod": 0.60, "cycles": 800},
    "48V — 200 Ah Lithium": {"capacity": 200, "voltage": 48, "technology": "Lithium", "dod": 0.80, "cycles": 2000},
}

# ── Régulateurs ──────────────────────────────────────────────────────────────
REGULATOR_CATALOG = {
    "[PWM]  10A —  50V":  {"type": "PWM",  "current_max": 10, "voltage_max": 50,  "efficiency": 0.75},
    "[PWM]  20A —  50V":  {"type": "PWM",  "current_max": 20, "voltage_max": 50,  "efficiency": 0.75},
    "[PWM]  30A —  50V":  {"type": "PWM",  "current_max": 30, "voltage_max": 50,  "efficiency": 0.75},
    "[MPPT] 20A — 100V":  {"type": "MPPT", "current_max": 20, "voltage_max": 100, "efficiency": 0.97},
    "[MPPT] 30A — 150V":  {"type": "MPPT", "current_max": 30, "voltage_max": 150, "efficiency": 0.97},
    "[MPPT] 40A — 150V":  {"type": "MPPT", "current_max": 40, "voltage_max": 150, "efficiency": 0.98},
    "[MPPT] 60A — 200V":  {"type": "MPPT", "current_max": 60, "voltage_max": 200, "efficiency": 0.98},
}

# ── Onduleurs ────────────────────────────────────────────────────────────────
INVERTER_CATALOG = {
    # 12 V DC
    "12V —  300 W (Onde modifiée)": {"power": 300,  "power_peak": 600,   "input_v": 12, "efficiency": 0.88, "wave": "Modifiée"},
    "12V —  500 W (Onde pure)":     {"power": 500,  "power_peak": 1000,  "input_v": 12, "efficiency": 0.90, "wave": "Pure"},
    "12V —  800 W (Onde pure)":     {"power": 800,  "power_peak": 1600,  "input_v": 12, "efficiency": 0.91, "wave": "Pure"},
    "12V — 1000 W (Onde pure)":     {"power": 1000, "power_peak": 2000,  "input_v": 12, "efficiency": 0.92, "wave": "Pure"},
    # 24 V DC
    "24V —  500 W (Onde pure)":     {"power": 500,  "power_peak": 1000,  "input_v": 24, "efficiency": 0.91, "wave": "Pure"},
    "24V — 1000 W (Onde pure)":     {"power": 1000, "power_peak": 2000,  "input_v": 24, "efficiency": 0.92, "wave": "Pure"},
    "24V — 1500 W (Onde pure)":     {"power": 1500, "power_peak": 3000,  "input_v": 24, "efficiency": 0.93, "wave": "Pure"},
    "24V — 2000 W (Onde pure)":     {"power": 2000, "power_peak": 4000,  "input_v": 24, "efficiency": 0.93, "wave": "Pure"},
    # 48 V DC
    "48V — 1000 W (Onde pure)":     {"power": 1000, "power_peak": 2000,  "input_v": 48, "efficiency": 0.93, "wave": "Pure"},
    "48V — 2000 W (Onde pure)":     {"power": 2000, "power_peak": 4000,  "input_v": 48, "efficiency": 0.94, "wave": "Pure"},
    "48V — 3000 W (Onde pure)":     {"power": 3000, "power_peak": 6000,  "input_v": 48, "efficiency": 0.95, "wave": "Pure"},
    "48V — 5000 W (Onde pure)":     {"power": 5000, "power_peak": 10000, "input_v": 48, "efficiency": 0.96, "wave": "Pure"},
}

# ── Charges par défaut ────────────────────────────────────────────────────────
DEFAULT_LOADS = [
    {"name": "Éclairage LED",      "power": 20, "qty": 3, "start_h": 18, "end_h": 23},
    {"name": "Ventilateur",        "power": 50, "qty": 1, "start_h": 8,  "end_h": 20},
    {"name": "Chargeur téléphone", "power": 10, "qty": 1, "start_h": 19, "end_h": 22},
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def batteries_for_voltage(voltage: int) -> dict:
    """Batteries compatibles avec la tension système."""
    return {k: v for k, v in BATTERY_CATALOG.items() if v["voltage"] == voltage}

def inverters_for_voltage(voltage: int) -> dict:
    """Onduleurs compatibles avec la tension système."""
    return {k: v for k, v in INVERTER_CATALOG.items() if v["input_v"] == voltage}

def regulators_for_pv(pv_isc: float, pv_voc: float) -> dict:
    """
    Régulateurs compatibles avec le champ PV :
    - courant max >= Isc_champ × 1.25
    - tension max >= Voc_champ
    Retourne aussi les incompatibles avec un flag 'compatible'.
    """
    result = {}
    for k, v in REGULATOR_CATALOG.items():
        required_i = pv_isc * 1.25
        ok_i = required_i <= v["current_max"]
        ok_v = pv_voc     <= v["voltage_max"]
        result[k] = {**v, "compatible": ok_i and ok_v,
                     "current_ok": ok_i, "voltage_ok": ok_v}
    return result