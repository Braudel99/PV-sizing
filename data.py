# data.py — Catalogues de matériels et constantes physiques

# ── Constantes physiques ─────────────────────────────────────────────────────
PERFORMANCE_RATIO = 0.75   # coefficient de performance système
PSH_DEFAULT       = 5.0    # heures de soleil pic par défaut

# ── Panneaux PV ──────────────────────────────────────────────────────────────
PV_CATALOG = {
    "Panneau 50 Wc":  {"power": 50,  "voc": 21.6, "isc": 3.11, "vmp": 17.6, "imp": 2.84},
    "Panneau 100 Wc": {"power": 100, "voc": 22.5, "isc": 5.96, "vmp": 18.2, "imp": 5.49},
    "Panneau 150 Wc": {"power": 150, "voc": 23.1, "isc": 8.70, "vmp": 18.9, "imp": 7.94},
    "Panneau 200 Wc": {"power": 200, "voc": 24.3, "isc": 10.98,"vmp": 20.1, "imp": 9.95},
    "Panneau 300 Wc": {"power": 300, "voc": 45.2, "isc": 9.01, "vmp": 37.8, "imp": 7.94},
}

# ── Batteries ────────────────────────────────────────────────────────────────
BATTERY_CATALOG = {
    "Batterie 50 Ah  — AGM":     {"capacity": 50,  "voltage": 12, "technology": "AGM",     "dod": 0.50, "cycles": 500},
    "Batterie 100 Ah — AGM":     {"capacity": 100, "voltage": 12, "technology": "AGM",     "dod": 0.50, "cycles": 600},
    "Batterie 150 Ah — GEL":     {"capacity": 150, "voltage": 12, "technology": "GEL",     "dod": 0.60, "cycles": 800},
    "Batterie 200 Ah — Lithium": {"capacity": 200, "voltage": 12, "technology": "Lithium", "dod": 0.80, "cycles": 2000},
}

# ── Régulateurs ──────────────────────────────────────────────────────────────
REGULATOR_CATALOG = {
    "[PWM]  10A — 50V":   {"type": "PWM",  "current_max": 10, "voltage_max": 50,  "efficiency": 0.75},
    "[PWM]  20A — 50V":   {"type": "PWM",  "current_max": 20, "voltage_max": 50,  "efficiency": 0.75},
    "[PWM]  30A — 50V":   {"type": "PWM",  "current_max": 30, "voltage_max": 50,  "efficiency": 0.75},
    "[MPPT] 20A — 100V":  {"type": "MPPT", "current_max": 20, "voltage_max": 100, "efficiency": 0.97},
    "[MPPT] 30A — 150V":  {"type": "MPPT", "current_max": 30, "voltage_max": 150, "efficiency": 0.97},
    "[MPPT] 40A — 150V":  {"type": "MPPT", "current_max": 40, "voltage_max": 150, "efficiency": 0.98},
    "[MPPT] 60A — 200V":  {"type": "MPPT", "current_max": 60, "voltage_max": 200, "efficiency": 0.98},
}

# ── Onduleurs ────────────────────────────────────────────────────────────────
INVERTER_CATALOG = {
    "Onduleur  300 W — 12V (Onde modifiée)": {"power": 300,  "power_peak": 600,  "input_v": 12, "efficiency": 0.88, "wave": "Modifiée"},
    "Onduleur  500 W — 12V (Onde pure)":     {"power": 500,  "power_peak": 1000, "input_v": 12, "efficiency": 0.90, "wave": "Pure"},
    "Onduleur 1000 W — 24V (Onde pure)":     {"power": 1000, "power_peak": 2000, "input_v": 24, "efficiency": 0.92, "wave": "Pure"},
    "Onduleur 1500 W — 24V (Onde pure)":     {"power": 1500, "power_peak": 3000, "input_v": 24, "efficiency": 0.93, "wave": "Pure"},
    "Onduleur 2000 W — 48V (Onde pure)":     {"power": 2000, "power_peak": 4000, "input_v": 48, "efficiency": 0.94, "wave": "Pure"},
    "Onduleur 3000 W — 48V (Onde pure)":     {"power": 3000, "power_peak": 6000, "input_v": 48, "efficiency": 0.95, "wave": "Pure"},
}

# ── Appareils de charge par défaut ───────────────────────────────────────────
DEFAULT_LOADS = [
    {"name": "Éclairage LED",       "power": 20,  "hours": 6.0},
    {"name": "Ventilateur",         "power": 50,  "hours": 8.0},
    {"name": "Chargeur téléphone",  "power": 10,  "hours": 3.0},
]
