"""SQLite-backed history storage for analyses."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.db")


class HistoryStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    language TEXT NOT NULL,
                    summary TEXT,
                    ai_model TEXT,
                    used_fallback INTEGER,
                    before_metrics TEXT,
                    after_metrics TEXT,
                    co2_projection TEXT,
                    session_emissions TEXT,
                    alternative_code TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert(
        self,
        *,
        language: str,
        summary: str,
        ai_model: str | None,
        used_fallback: bool,
        before_metrics: Dict[str, Any],
        after_metrics: Dict[str, Any],
        co2_projection: Dict[str, Any],
        session_emissions: Dict[str, Any],
        alternative_code: str,
    ) -> int:
        payload = (
            language,
            summary,
            ai_model,
            int(used_fallback),
            json.dumps(before_metrics),
            json.dumps(after_metrics),
            json.dumps(co2_projection),
            json.dumps(session_emissions),
            alternative_code,
            datetime.now(timezone.utc).isoformat(),
        )
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO history (
                    language, summary, ai_model, used_fallback, before_metrics,
                    after_metrics, co2_projection, session_emissions, alternative_code, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            conn.commit()
            return int(cursor.lastrowid)

    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, language, summary, ai_model, used_fallback, before_metrics,
                       after_metrics, co2_projection, session_emissions, created_at
                FROM history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        history = []
        for row in rows:
            (
                record_id,
                language,
                summary,
                ai_model,
                used_fallback,
                before_metrics,
                after_metrics,
                co2_projection,
                session_emissions,
                created_at,
            ) = row
            history.append(
                {
                    "id": record_id,
                    "language": language,
                    "summary": summary,
                    "ai_model": ai_model,
                    "used_fallback": bool(used_fallback),
                    "before_metrics": json.loads(before_metrics or "{}"),
                    "after_metrics": json.loads(after_metrics or "{}"),
                    "co2_projection": json.loads(co2_projection or "{}"),
                    "session_emissions": json.loads(session_emissions or "{}"),
                    "created_at": created_at,
                }
            )
        return history

    def dashboard(self, limit: int = 20, max_points: int = 12) -> Dict[str, Any]:
        """Return aggregated stats for dashboard visualizations."""

        entries = self.recent(limit=limit)
        if not entries:
            return {
                "timeseries": [],
                "totals": {
                    "runs": 0,
                    "co2_saved_total": 0.0,
                    "co2_saved_avg": 0.0,
                    "compile_time_saved_total": 0.0,
                    "compile_time_saved_avg": 0.0,
                    "latest_summary": "",
                },
                "report": [],
            }

        def _safe_number(value: Any, default: float = 0.0) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        total_co2 = 0.0
        total_compile = 0.0
        timeseries: List[Dict[str, Any]] = []

        # ensure chronological order for charts
        for entry in reversed(entries):
            before_co2 = _safe_number(entry.get("co2_projection", {}).get("before", {}).get("co2_kg"))
            after_co2 = _safe_number(entry.get("co2_projection", {}).get("after", {}).get("co2_kg"))
            before_complexity = _safe_number(entry.get("before_metrics", {}).get("estimated_complexity"))
            after_complexity = _safe_number(entry.get("after_metrics", {}).get("estimated_complexity"))

            co2_saved = max(before_co2 - after_co2, 0.0)
            compile_saved = max(before_complexity - after_complexity, 0.0)

            total_co2 += co2_saved
            total_compile += compile_saved

            timeseries.append(
                {
                    "id": entry.get("id"),
                    "created_at": entry.get("created_at"),
                    "language": entry.get("language"),
                    "summary": entry.get("summary"),
                    "co2_saved": round(co2_saved, 4),
                    "compile_time_saved": round(compile_saved, 2),
                }
            )

        run_count = len(entries)
        # trim to the most recent `max_points` items while keeping chronological order
        if max_points > 0 and len(timeseries) > max_points:
            timeseries = timeseries[-max_points:]

        totals = {
            "runs": run_count,
            "co2_saved_total": round(total_co2, 4),
            "co2_saved_avg": round(total_co2 / run_count, 4) if run_count else 0.0,
            "compile_time_saved_total": round(total_compile, 2),
            "compile_time_saved_avg": round(total_compile / run_count, 2) if run_count else 0.0,
            "latest_summary": entries[0].get("summary", ""),
        }

        report = [
            f"Last {run_count} runs avoided {totals['co2_saved_total']:.4f} kg CO₂.",
            f"Average compile-time complexity saved: {totals['compile_time_saved_avg']:.2f} points.",
        ]

        top_run = max(timeseries, key=lambda item: item["co2_saved"], default=None)
        if top_run and top_run["co2_saved"] > 0:
            report.append(
                f"Run #{top_run['id']} ({top_run['language']}) saved the most CO₂ at {top_run['co2_saved']:.4f} kg."
            )

        if totals["latest_summary"]:
            report.append(f"Most recent summary: {totals['latest_summary']}")

        return {
            "timeseries": timeseries,
            "totals": totals,
            "report": report,
        }

