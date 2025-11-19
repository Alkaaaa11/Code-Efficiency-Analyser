"""Rudimentary CO2 estimation utilities."""

from __future__ import annotations

from typing import Dict

# Average data center emissions factor (gCO2eq per kWh)
GLOBAL_AVG_CO2_PER_KWH = 475.0

def _estimate_energy_kwh(lines_of_code: int, complexity: float) -> float:
    # Scaling constant chosen for demo purposes
    return round(max(lines_of_code, 1) * max(complexity, 1) / 50000, 4)


def estimate_co2_impact(report: Dict[str, float]) -> Dict[str, float]:
    energy = _estimate_energy_kwh(
        int(report.get("lines_of_code", 0)), float(report.get("estimated_complexity", 0))
    )
    co2 = round(energy * GLOBAL_AVG_CO2_PER_KWH / 1000, 4)
    return {
        "energy_kwh": energy,
        "co2_kg": co2,
    }
