# Code Efficiency Studio

Full-stack experiment that inspects Python or Java snippets, generates optimization ideas, and shows the impact on energy/CO₂ before and after an AI-guided refactor.

## Features
- Paste Python or Java code and receive complexity heuristics (loops, conditionals, repeated blocks, etc.).
- Optional Ollama-powered DeepSeek suggestions (local `deepseek-coder:1.3b`) with a deterministic fallback when the model is unavailable.
- Real-time CodeCarbon measurements that capture actual backend energy/CO₂ usage per analysis request, alongside heuristic projections before and after optimization.
- Comparative dashboard showing before/after metrics, AI insights, measured emissions, and suggested code.
- Built-in SQLite history log with a recent-analyses panel in the UI so you can audit previous runs.
- Flask backend with a static HTML/CSS/JS frontend (no build step required).

## Project Layout
```
backend/            # Flask API + heuristics + Ollama client
frontend/           # Static UI (index.html, styles.css, main.js)
```

## Backend Setup
1. Create a virtual environment and install dependencies:
   ```bash
   cd /Users/alka/Desktop/Code\ -\ Efficiency/backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Ensure [Ollama](https://ollama.ai) is installed and the `deepseek-coder:1.3b` model is pulled:
   ```bash
   ollama pull deepseek-coder:1.3b
   ollama run deepseek-coder:1.3b  # starts the model so the API can call it
   ```
   The backend points to `http://127.0.0.1:11434` by default. Override with `export OLLAMA_BASE_URL=http://host:port` if needed.
3. CodeCarbon runs in process automatically. Set `COUNTRY_ISO_CODE` if you want region-specific factors; otherwise global defaults are used.
4. Run the API:
   ```bash
   flask --app app run --port 5000 --debug
   ```

## Frontend Usage
Open `frontend/index.html` in a browser (or serve via `python3 -m http.server` inside the `frontend` directory). Update `BACKEND_URL` in `main.js` if the API runs elsewhere.

## API Contract
### `POST /api/analyze`
Request body:
```json
{
  "code": "string",
  "language": "python" | "java"
}
```
Response body (abridged):
```json
{
  "analysis": {
    "before": {},
    "after": {},
    "delta": {}
  },
  "co2": {
    "before": {"energy_kwh": 0.0, "co2_kg": 0.0},
    "after": {"energy_kwh": 0.0, "co2_kg": 0.0},
    "energy_saved_kwh": 0.0
  },
  "session_emissions": {"energy_kwh": 0.0, "co2_kg": 0.0, "duration_s": 0.0},
  "suggestion": {
    "summary": "",
    "confidence": "",
    "analysis_insights": [],
    "ai_model_used": "",
    "used_fallback": false,
    "alternative_code": ""
  },
  "alternative_code": "",
  "history": [...]
}
```

### `GET /api/history`
Returns the 25 most recent analyses pulled from the SQLite log.

The backend automatically persists each request in `backend/data/history.db`.

## Next Ideas
- Swap heuristic CO₂ math with [codecarbon](https://mlco2.github.io/codecarbon/).
- Persist historical analyses for longitudinal reporting.
- Add unit tests around analysis helpers and integrate a richer AST-based optimizer.
