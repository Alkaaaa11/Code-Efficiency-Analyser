# Code Efficiency Studio

Full-stack application that analyzes code efficiency, generates optimization suggestions, and tracks CO₂ emissions impact. Supports single file analysis (paste or upload) and full project analysis via ZIP upload.

## Features

### Single File Analysis
- **Paste or Upload Code**: Paste code directly or upload individual code files (.py, .java, .js, .jsx, .html, .css)
- **Multi-Language Support**: Python, Java, JavaScript, HTML, and CSS
- **Complexity Analysis**: Heuristic analysis of loops, conditionals, functions, duplicates, and code complexity
- **AI-Powered Suggestions**: Optional Ollama-powered DeepSeek suggestions (local `deepseek-coder:1.3b`) with deterministic fallback
- **CO₂ Impact Tracking**: Estimates energy consumption and CO₂ emissions before and after optimization
- **CodeCarbon Integration**: Real-time measurements of actual backend energy/CO₂ usage per analysis

### Project Analysis
- **ZIP Upload**: Upload entire project folders (up to 250 MB) as ZIP files
- **Multi-File Analysis**: Analyzes all supported files in the project
- **Interconnection Detection**: Automatically detects file dependencies and interconnections
  - Python: `import` and `from ... import` statements
  - Java: `import` statements
  - JavaScript: `import`, `require()`, dynamic imports
  - HTML: `<script src>` and `<link href>` tags
  - CSS: `@import` statements
- **Aggregate Metrics**: Project-wide statistics including total LOC, complexity, and languages used
- **Optimization Suggestions**: AI suggestions for top complexity files

### Dashboard & History
- **Impact Dashboard**: Visual charts showing CO₂ saved and compile time improvements over time
- **History Tracking**: SQLite-based history log with recent analyses panel
- **Real-time Updates**: Dashboard refreshes automatically after each analysis

## Project Layout
```
Code-Efficiency-Analyser/
├── backend/                    # Flask API + analysis modules
│   ├── analysis/              # Code analysis modules
│   │   ├── complexity.py      # Complexity heuristics
│   │   ├── co2.py             # CO₂ estimation
│   │   ├── suggestions.py     # AI suggestion engine
│   │   └── project_analyzer.py # Multi-file project analysis
│   ├── services/              # Backend services
│   │   ├── history_store.py   # SQLite history storage
│   │   ├── tracking.py        # CodeCarbon integration
│   │   └── ollama_client.py   # Ollama API client
│   ├── app.py                 # Flask application
│   └── requirements.txt       # Python dependencies
└── frontend/                   # Static UI
    ├── index.html             # Main analysis page
    ├── dashboard.html         # Dashboard page
    ├── main.js                # Analysis page logic
    ├── dashboard.js           # Dashboard logic
    └── styles.css             # Styling (white/blue theme)
```

## Backend Setup

1. **Create a virtual environment and install dependencies:**
   ```bash
   cd Code-Efficiency-Analyser/backend
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Optional: Setup Ollama for AI suggestions**
   - Install [Ollama](https://ollama.ai)
   - Pull the DeepSeek model:
     ```bash
     ollama pull deepseek-coder:1.3b
     ```
   - The backend points to `http://127.0.0.1:11434` by default
   - Override with `export OLLAMA_BASE_URL=http://host:port` if needed
   - **Note**: The app works without Ollama using heuristic fallbacks

3. **CodeCarbon Configuration**
   - CodeCarbon runs automatically in process
   - Set `COUNTRY_ISO_CODE` environment variable for region-specific factors
   - Otherwise, global defaults are used

4. **Run the Flask API:**
   ```bash
   cd backend
   flask --app app run --port 5000 --debug
   ```
   Or directly:
   ```bash
   python app.py
   ```

## Frontend Usage

1. **Open the application:**
   - Simply open `frontend/index.html` in a web browser
   - Or serve via HTTP server:
     ```bash
     cd frontend
     python3 -m http.server 8000
     # Then open http://localhost:8000 in browser
     ```

2. **Update backend URL (if needed):**
   - Edit `BACKEND_URL` in `frontend/main.js` if API runs on different host/port
   - Default: `http://localhost:5000`

## API Endpoints

### `POST /api/analyze`
Analyze a single code snippet.

**Request:**
```json
{
  "code": "string",
  "language": "python" | "java" | "javascript" | "html" | "css"
}
```

**Response:**
```json
{
  "analysis": {
    "before": { /* complexity metrics */ },
    "after": { /* optimized metrics */ },
    "delta": { /* differences */ }
  },
  "co2": {
    "before": {"energy_kwh": 0.0, "co2_kg": 0.0},
    "after": {"energy_kwh": 0.0, "co2_kg": 0.0},
    "energy_saved_kwh": 0.0
  },
  "session_emissions": {"energy_kwh": 0.0, "co2_kg": 0.0, "duration_s": 0.0},
  "suggestion": {
    "summary": "Optimization summary",
    "confidence": "high/medium/low",
    "analysis_insights": [ /* array of insights */ ],
    "ai_model_used": "deepseek-coder:1.3b" | null,
    "used_fallback": false,
    "alternative_code": "optimized code"
  },
  "alternative_code": "string",
  "history": [ /* recent analyses */ ]
}
```

### `POST /api/analyze-project`
Analyze an entire project from a ZIP file.

**Request:** `multipart/form-data` with `file` field (ZIP archive, max 250 MB)

**Response:**
```json
{
  "project_analysis": {
    "files": { /* file path -> analysis data */ },
    "interconnections": [ /* dependency graph */ ],
    "summary": {
      "total_files": 10,
      "total_lines_of_code": 1500,
      "total_complexity": 45.2,
      "languages": ["python", "javascript"],
      "interconnection_count": 8
    }
  },
  "co2": { /* aggregate CO₂ impact */ },
  "session_emissions": { /* measured emissions */ },
  "suggestions": [ /* top file suggestions */ ]
}
```

### `GET /api/history`
Returns the 25 most recent analyses from SQLite log.

### `GET /api/dashboard`
Returns aggregated dashboard statistics for visualization.

### `GET /api/health`
Health check endpoint.

## Data Storage

- **SQLite Database**: `backend/data/history.db`
- Automatically created on first run
- Stores all analysis results, metrics, and emissions data

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no build step)
- **Database**: SQLite
- **Energy Tracking**: CodeCarbon
- **AI Suggestions**: Ollama (optional, with heuristic fallback)
- **Visualization**: Chart.js (dashboard only)

## Color Scheme

The application uses a clean white background with blue accents:
- **Background**: Pure white (#ffffff)
- **Primary Text**: Dark gray (#1e2937)
- **Accents**: Blue shades (#2563eb, #3b82f6)
- **Borders**: Light gray (#cbd5e1, #e2e8f0)
- **Cards**: Light gray background (#f8fafc)

## Future Enhancements

- [ ] Support for more languages (TypeScript, C++, Go, etc.)
- [ ] AST-based code optimization
- [ ] Real-time collaboration features
- [ ] Export analysis reports (PDF/JSON)
- [ ] Integration with CI/CD pipelines
- [ ] Advanced dependency visualization
