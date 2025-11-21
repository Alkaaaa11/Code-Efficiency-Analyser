"""Suggestion engine that mixes heuristics with optional generative AI."""

from __future__ import annotations

import json
import textwrap
from typing import Dict, List, Optional

try:  # pragma: no cover - import shim for running from repo root or backend dir
    from services.ollama_client import OllamaClient
except ModuleNotFoundError:  # type: ignore
    from backend.services.ollama_client import OllamaClient  # type: ignore


class SuggestionEngine:
    def __init__(self, ai_client: Optional[OllamaClient] = None) -> None:
        self.ai_client = ai_client or OllamaClient()

    def _build_prompt(self, code: str, language: str, metrics: Dict[str, float]) -> str:
        schema = textwrap.dedent(
            """
            {
              "summary": "<=200 characters explaining the optimization",
              "confidence": "high|medium|low",
              "analysis": [
                {
                  "issue": "short title of an inefficiency",
                  "impact": "one sentence describing why it matters",
                  "action": "specific fix you applied"
                }
              ],
              "alternative_code": "the improved code snippet using \\n for new lines, no markdown fences"
            }
            """
        ).strip()
        return textwrap.dedent(
            f"""
            You are a senior {language} engineer. Review the code and output ONLY strict JSON
            that matches the schema below. Do not include markdown, comments, or prose outside
            the JSON. Escape newline characters as "\\n" inside strings.

            Schema:
            {schema}

            Current metrics: {metrics}

            <code>
            {code}
            </code>
            """
        ).strip()

    @staticmethod
    def _fallback_heuristic(code: str) -> Dict[str, object]:
        lines = code.splitlines()
        optimized_lines = []
        seen = set()
        for line in lines:
            stripped = line.strip()
            if stripped and stripped in seen:
                continue
            optimized_lines.append(line)
            if stripped:
                seen.add(stripped)
        summary = (
            "Removed duplicate lines and recommended extracting repeated logic into helper functions."
        )
        return {
            "summary": summary,
            "confidence": "low",
            "analysis_insights": [
                {
                    "issue": "Duplicate lines",
                    "impact": "Redundant operations waste CPU cycles and energy.",
                    "action": "Keep one copy per repeated block or extract helpers.",
                }
            ],
            "alternative_code": "\n".join(optimized_lines) or code,
            "ai_model_used": None,
            "used_fallback": True,
        }

    @staticmethod
    def _parse_json_output(ai_output: str) -> Optional[Dict[str, object]]:
        trimmed = ai_output.strip()
        if not trimmed:
            return None
        # Attempt to isolate JSON if extraneous text sneaks in.
        if not trimmed.startswith("{"):
            start = trimmed.find("{")
            end = trimmed.rfind("}")
            if start == -1 or end == -1:
                return None
            trimmed = trimmed[start : end + 1]
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_analysis(items: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        normalized = []
        if not items:
            return normalized
        for entry in items:
            if not isinstance(entry, dict):
                continue
            normalized.append(
                {
                    "issue": str(entry.get("issue", "")).strip() or "Optimization",
                    "impact": str(entry.get("impact", "")).strip() or "Impact not provided.",
                    "action": str(entry.get("action", "")).strip() or "Action not provided.",
                }
            )
        return normalized

    def generate(self, code: str, language: str, metrics: Dict[str, float]) -> Dict[str, object]:
        prompt = self._build_prompt(code, language, metrics)
        ai_output = None
        if self.ai_client.is_configured():
            try:
                ai_output = self.ai_client.generate(prompt)
            except Exception as exc:  # noqa: BLE001
                ai_output = f"Model call failed: {exc}"
        if not ai_output:
            return self._fallback_heuristic(code)

        parsed = self._parse_json_output(ai_output)
        if not parsed:
            return self._fallback_heuristic(code)

        alternative_code = str(parsed.get("alternative_code") or "").replace("\\n", "\n").strip()
        if not alternative_code:
            alternative_code = code

        return {
            "summary": str(parsed.get("summary") or "Model suggestion").strip(),
            "confidence": str(parsed.get("confidence") or "medium").strip(),
            "analysis_insights": self._normalize_analysis(parsed.get("analysis")),
            "alternative_code": alternative_code,
            "ai_model_used": self.ai_client.model if self.ai_client.is_configured() else None,
            "used_fallback": False,
        }
