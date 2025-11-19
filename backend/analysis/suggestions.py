"""Suggestion engine that mixes heuristics with optional generative AI."""

from __future__ import annotations

import re
import textwrap
from typing import Dict, Optional

from backend.services.huggingface_client import HuggingFaceClient

CODE_BLOCK_PATTERN = re.compile(r"```(?:python|java|)(.*?)```", re.DOTALL)


class SuggestionEngine:
    def __init__(self, ai_client: Optional[HuggingFaceClient] = None) -> None:
        self.ai_client = ai_client or HuggingFaceClient()

    def _build_prompt(self, code: str, language: str, metrics: Dict[str, float]) -> str:
        bullet_points = textwrap.dedent(
            f"""
            You are a senior {language} engineer. Analyze the given code and propose a more
            efficient alternative that removes redundant loops, extracts repeated logic into
            helper functions, and keeps behavior identical.

            Current metrics: {metrics}
            Respond with a short summary followed by a fenced code block containing ONLY the
            improved code in the same language.
            """
        ).strip()
        return f"{bullet_points}\n\n<code>\n{code}\n</code>"

    @staticmethod
    def _extract_code_block(ai_output: str) -> Optional[str]:
        match = CODE_BLOCK_PATTERN.search(ai_output)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _fallback_heuristic(code: str) -> Dict[str, str]:
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
            "Removed exact duplicate lines and encouraged extracting repeated logic into"
            " helper functions. Consider parameterizing repeated loops."
        )
        return {
            "summary": summary,
            "alternative_code": "\n".join(optimized_lines) or code,
            "ai_model_used": None,
            "used_fallback": True,
        }

    def generate(self, code: str, language: str, metrics: Dict[str, float]) -> Dict[str, str]:
        prompt = self._build_prompt(code, language, metrics)
        ai_output = None
        if self.ai_client.is_configured():
            try:
                ai_output = self.ai_client.generate(prompt)
            except Exception as exc:  # noqa: BLE001
                ai_output = f"Model call failed: {exc}"
        if not ai_output:
            return self._fallback_heuristic(code)

        code_block = self._extract_code_block(ai_output)
        alternative_code = code_block or ai_output.strip()
        summary = ai_output.split("```", 1)[0].strip().splitlines()
        summary_text = " ".join(summary[:3]).strip() or "Model suggestion"
        return {
            "summary": summary_text,
            "alternative_code": alternative_code,
            "ai_model_used": self.ai_client.model if self.ai_client.is_configured() else None,
            "used_fallback": not bool(code_block),
        }
