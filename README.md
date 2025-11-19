# Code Efficiency Studio

Full-stack experiment that inspects Python or Java snippets, generates optimization ideas, and shows the impact on energy/CO₂ before and after an AI-guided refactor.

## Features
- Paste Python or Java code and receive complexity heuristics (loops, conditionals, repeated blocks, etc.).
- Optional Hugging Face inference call (StarCoder by default) to propose cleaner code; falls back to deterministic heuristics when no API token is set.
- CO₂/energy estimation based on code size & complexity to highlight sustainability wins.
- Comparative dashboard showing before/after metrics, deltas, and suggested code.
- Flask backend with a static HTML/CSS/JS frontend (no build step required).

## Project Layout
```
backend/            # Flask API + heuristics + HF client
frontend/           # Static UI (index.html, styles.css, main.js)
```

## Backend Setup
1. Create a virtual environment and install dependencies:
   ```bash
   cd /Users/alka/Desktop/Code\ -\ Efficiency/backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. (Optional) Export a Hugging Face API token for better suggestions:
   ```bash
   export HF_API_TOKEN=hf_your_token
   ```
3. Run the API:
   ```bash
   flask --app app run --port 5000 --debug
   ```

## Frontend Usage
Open `frontend/index.html` in a browser (or serve via `python3 -m http.server` inside the `frontend` directory). Update `BACKEND_URL` in `main.js` if the API runs elsewhere.

## API Contract
`POST /api/analyze`
```json
{
  "code": "string",  // required
  "language": "python" | "java"
}
```
Response contains analysis (before/after/delta), CO₂ stats, and the alternative code.

## Next Ideas
- Swap heuristic CO₂ math with [codecarbon](https://mlco2.github.io/codecarbon/).
- Persist historical analyses for longitudinal reporting.
- Add unit tests around analysis helpers and integrate a richer AST-based optimizer.
