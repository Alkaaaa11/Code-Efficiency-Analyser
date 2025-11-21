"""Helpers for measuring emissions with CodeCarbon."""

from __future__ import annotations

import time
from dataclasses import dataclass
import inspect
from typing import Dict, Optional

from codecarbon import EmissionsTracker


@dataclass
class EmissionResult:
    energy_kwh: float
    co2_kg: float
    duration_s: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "energy_kwh": round(self.energy_kwh, 6),
            "co2_kg": round(self.co2_kg, 6),
            "duration_s": round(self.duration_s, 3),
        }


class CodeCarbonSession:
    """Context manager that wraps the CodeCarbon tracker."""

    def __init__(self, country_iso_code: Optional[str] = None) -> None:
        self.country_iso_code = country_iso_code
        self._tracker: Optional[EmissionsTracker] = None
        self._start_time: Optional[float] = None
        self._energy_kwh: float = 0.0
        self._co2_kg: float = 0.0

    def __enter__(self) -> "CodeCarbonSession":
        self._start_time = time.perf_counter()
        tracker_kwargs = {
            "measure_power_secs": 1,
            "tracking_mode": "process",
            "log_level": "error",
            "save_to_file": False,
        }
        init_params = inspect.signature(EmissionsTracker.__init__).parameters
        if self.country_iso_code and "country_iso_code" in init_params:
            tracker_kwargs["country_iso_code"] = self.country_iso_code
        self._tracker = EmissionsTracker(**tracker_kwargs)
        self._tracker.start()
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        if self._tracker is not None:
            emissions = self._tracker.stop()
            if emissions is not None:
                self._co2_kg = float(emissions)
                data = getattr(self._tracker, "final_emissions_data", {}) or {}
                if hasattr(data, "energy_consumed"):
                    self._energy_kwh = float(getattr(data, "energy_consumed") or 0.0)
                elif isinstance(data, dict):
                    self._energy_kwh = float(data.get("energy_consumed", 0.0))
        if self._start_time is not None:
            self._duration = time.perf_counter() - self._start_time

    def result(self) -> EmissionResult:
        duration = getattr(self, "_duration", 0.0)
        return EmissionResult(
            energy_kwh=self._energy_kwh,
            co2_kg=self._co2_kg,
            duration_s=duration,
        )

