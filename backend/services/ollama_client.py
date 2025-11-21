"""Lightweight Ollama client for local DeepSeek models."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class OllamaClient:
    def __init__(
        self,
        model: str = "deepseek-coder:1.3b",
        base_url: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        default_base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = model
        self.base_url = (base_url or default_base).rstrip("/")
        self.timeout = timeout
        temperature = os.getenv("OLLAMA_TEMPERATURE")
        try:
            self.temperature = float(temperature) if temperature is not None else 0.2
        except ValueError:
            self.temperature = 0.2

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    def generate(self, prompt: str, max_new_tokens: int = 400) -> Optional[str]:
        if not self.is_configured():
            return None
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "num_predict": max_new_tokens,
            },
        }
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data.get("response")
        return None

