"""Heuristic code complexity analysis utilities."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Sequence

LOOP_KEYWORDS = {
    "python": ["for", "while"],
    "java": ["for", "while", "do"],
}

CONDITIONAL_KEYWORDS = {
    "python": ["if", "elif", "else", "match"],
    "java": ["if", "else", "switch", "case"],
}

FUNCTION_KEYWORDS = {
    "python": ["def", "class"],
    "java": ["class", "void", "public", "private", "protected"],
}

SUPPORTED_LANGUAGES = {"python", "java"}


@dataclass
class ComplexityReport:
    language: str
    lines_of_code: int
    loops: int
    conditionals: int
    functions: int
    duplicate_lines: int
    repeated_sequences: int
    estimated_complexity: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "loops": self.loops,
            "conditionals": self.conditionals,
            "functions": self.functions,
            "duplicate_lines": self.duplicate_lines,
            "repeated_sequences": self.repeated_sequences,
            "estimated_complexity": round(self.estimated_complexity, 2),
        }


def _sanitize_language(language: str) -> str:
    normalized = (language or "").strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. Supported: {sorted(SUPPORTED_LANGUAGES)}"
        )
    return normalized


def _count_keywords(code: str, keywords: Sequence[str]) -> int:
    if not keywords:
        return 0
    pattern = r"\\b(" + "|".join(re.escape(keyword) for keyword in keywords) + r")\\b"
    return len(re.findall(pattern, code))


def _count_duplicate_lines(lines: List[str]) -> int:
    counter = Counter(line for line in lines if line)
    duplicate_total = sum(count - 1 for count in counter.values() if count > 1)
    return duplicate_total


def _count_repeated_sequences(lines: List[str], window: int = 3) -> int:
    if len(lines) < window:
        return 0
    sequences = Counter(
        tuple(lines[i : i + window])
        for i in range(len(lines) - window + 1)
        if all(line for line in lines[i : i + window])
    )
    return sum(count - 1 for count in sequences.values() if count > 1)


def _estimate_complexity(loops: int, conditionals: int, functions: int, duplicates: int) -> float:
    base = 1 + loops * 1.8 + conditionals * 1.2 + functions * 0.5
    penalty = duplicates * 0.7
    return base + penalty


def analyze_code_complexity(code: str, language: str) -> Dict[str, float]:
    """Return a simple heuristics-based complexity report."""

    normalized_language = _sanitize_language(language)
    normalized_lines = [line.strip() for line in code.splitlines()]
    lines_of_code = sum(1 for line in normalized_lines if line)

    loops = _count_keywords(code, LOOP_KEYWORDS[normalized_language])
    conditionals = _count_keywords(code, CONDITIONAL_KEYWORDS[normalized_language])
    functions = _count_keywords(code, FUNCTION_KEYWORDS[normalized_language])
    duplicate_lines = _count_duplicate_lines(normalized_lines)
    repeated_sequences = _count_repeated_sequences(normalized_lines)

    report = ComplexityReport(
        language=normalized_language,
        lines_of_code=lines_of_code,
        loops=loops,
        conditionals=conditionals,
        functions=functions,
        duplicate_lines=duplicate_lines,
        repeated_sequences=repeated_sequences,
        estimated_complexity=_estimate_complexity(
            loops, conditionals, functions, duplicate_lines + repeated_sequences
        ),
    )
    return report.as_dict()


def summarize_differences(before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
    """Provide a delta summary between two complexity reports."""

    keys = {
        "lines_of_code",
        "loops",
        "conditionals",
        "functions",
        "duplicate_lines",
        "repeated_sequences",
        "estimated_complexity",
    }
    return {key: round(before.get(key, 0) - after.get(key, 0), 2) for key in keys}
