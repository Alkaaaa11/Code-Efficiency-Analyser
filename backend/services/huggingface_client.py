"""Lightweight Hugging Face Inference API client."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests


class HuggingFaceClient:
    def __init__(
        self,
        model: str = "bigcode/starcoder",
        api_token: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.model = model
        self.api_token = api_token or os.getenv("HF_API_TOKEN")
        self.timeout = timeout
        self.endpoint = f"https://api-inference.huggingface.co/models/{self.model}"

    def is_configured(self) -> bool:
        return bool(self.api_token)

    def generate(self, prompt: str, max_new_tokens: int = 400) -> Optional[str]:
        if not self.is_configured():
            return None
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0.2,
                "return_full_text": False,
            },
        }
        response = requests.post(self.endpoint, headers=headers, data=json.dumps(payload), timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text")
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        return None
