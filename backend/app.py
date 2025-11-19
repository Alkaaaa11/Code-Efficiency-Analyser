from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

from analysis import (
    SuggestionEngine,
    analyze_code_complexity,
    estimate_co2_impact,
    summarize_differences,
)

app = Flask(__name__)
CORS(app)
suggestion_engine = SuggestionEngine()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze_code():
    payload = request.get_json(force=True, silent=True) or {}
    code = payload.get("code", "")
    language = payload.get("language", "python")

    if not code.strip():
        return jsonify({"error": "Code input is required."}), 400

    try:
        before_metrics = analyze_code_complexity(code, language)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    suggestion = suggestion_engine.generate(code, language, before_metrics)
    alternative_code = suggestion.get("alternative_code", code)

    try:
        after_metrics = analyze_code_complexity(alternative_code, language)
    except ValueError:
        after_metrics = before_metrics

    co2_before = estimate_co2_impact(before_metrics)
    co2_after = estimate_co2_impact(after_metrics)

    comparison = summarize_differences(before_metrics, after_metrics)
    energy_savings = round(max(co2_before["energy_kwh"] - co2_after["energy_kwh"], 0), 4)

    response = {
        "analysis": {
            "before": before_metrics,
            "after": after_metrics,
            "delta": comparison,
        },
        "co2": {
            "before": co2_before,
            "after": co2_after,
            "energy_saved_kwh": energy_savings,
        },
        "suggestion": suggestion,
        "alternative_code": alternative_code,
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
