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

