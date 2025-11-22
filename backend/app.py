from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from analysis import SuggestionEngine, analyze_code_complexity, estimate_co2_impact, summarize_differences
from analysis.project_analyzer import analyze_project

try:  # pragma: no cover - allow running from repo root or backend dir
    from services.history_store import HistoryStore
    from services.tracking import CodeCarbonSession
except ModuleNotFoundError:  # type: ignore
    from backend.services.history_store import HistoryStore  # type: ignore
    from backend.services.tracking import CodeCarbonSession  # type: ignore

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300 MB max file size
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()

suggestion_engine = SuggestionEngine()
history_store = HistoryStore()


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

    with CodeCarbonSession() as session:
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

    emissions = session.result().as_dict()

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
        "session_emissions": emissions,
        "suggestion": suggestion,
        "alternative_code": alternative_code,
    }
    history_store.insert(
        language=language,
        summary=str(suggestion.get("summary", "")),
        ai_model=suggestion.get("ai_model_used"),
        used_fallback=bool(suggestion.get("used_fallback")),
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        co2_projection=response["co2"],
        session_emissions=emissions,
        alternative_code=alternative_code,
    )
    response["history"] = history_store.recent(limit=10)
    return jsonify(response)


@app.get("/api/history")
def list_history():
    return jsonify({"items": history_store.recent(limit=25)})


@app.get("/api/dashboard")
def dashboard_summary():
    return jsonify(history_store.dashboard(limit=25))


def extract_zip_file(zip_path: str, extract_to: str) -> dict[str, str]:
    """Extract zip file and return dict of file paths to content."""
    files_content: dict[str, str] = {}
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Get list of file names in zip
        file_list = zip_ref.namelist()
        
        # Extract all files
        zip_ref.extractall(extract_to)
        
        # Read supported file types
        supported_extensions = {".py", ".java", ".js", ".jsx", ".html", ".htm", ".css"}
        
        for file_name in file_list:
            full_path = os.path.join(extract_to, file_name)
            
            # Skip directories and unsupported files
            if os.path.isdir(full_path):
                continue
            
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in supported_extensions:
                continue
            
            # Skip files that are too large (safety check)
            if os.path.getsize(full_path) > 10 * 1024 * 1024:  # 10 MB per file
                continue
            
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # Use relative path from extract root
                    rel_path = os.path.relpath(full_path, extract_to)
                    files_content[rel_path] = content
            except Exception:
                continue
    
    return files_content


@app.post("/api/analyze-project")
def analyze_project_upload():
    """Handle zip file upload and analyze entire project."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only ZIP files are supported"}), 400
    
    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    temp_zip_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(temp_zip_path)
    
    # Create temporary extraction directory
    extract_dir = tempfile.mkdtemp()
    
    try:
        # Extract zip file
        project_files = extract_zip_file(temp_zip_path, extract_dir)
        
        if not project_files:
            return jsonify({"error": "No supported files found in ZIP archive"}), 400
        
        # Analyze project
        with CodeCarbonSession() as session:
            project_analysis = analyze_project(project_files, project_root=extract_dir)
            
            # Calculate aggregate CO2 impact
            total_before_complexity = sum(
                f.get("metrics", {}).get("estimated_complexity", 0)
                for f in project_analysis["files"].values()
            )
            total_before_loc = project_analysis["summary"]["total_lines_of_code"]
            
            # Estimate CO2 for entire project
            aggregate_metrics = {
                "lines_of_code": total_before_loc,
                "estimated_complexity": total_before_complexity,
            }
            co2_before = estimate_co2_impact(aggregate_metrics)
            
            # Generate suggestions for key files (top 5 by complexity)
            file_complexities = [
                (path, f.get("metrics", {}).get("estimated_complexity", 0))
                for path, f in project_analysis["files"].items()
            ]
            file_complexities.sort(key=lambda x: x[1], reverse=True)
            
            suggestions = []
            for filepath, _ in file_complexities[:5]:
                file_data = project_analysis["files"][filepath]
                if "error" in file_data:
                    continue
                
                language = file_data["language"]
                content = project_files.get(filepath, "")
                metrics = file_data["metrics"]
                
                try:
                    suggestion = suggestion_engine.generate(content, language, metrics)
                    suggestions.append({
                        "file": filepath,
                        "suggestion": suggestion,
                    })
                except Exception:
                    pass
        
        emissions = session.result().as_dict()
        
        response = {
            "project_analysis": project_analysis,
            "co2": {
                "before": co2_before,
                "energy_saved_kwh": 0.0,  # Would need after analysis for savings
            },
            "session_emissions": emissions,
            "suggestions": suggestions,
        }
        
        # Store in history (simplified)
        history_store.insert(
            language="multi",
            summary=f"Project: {len(project_files)} files, {project_analysis['summary']['total_lines_of_code']} LOC",
            ai_model=None,
            used_fallback=True,
            before_metrics=aggregate_metrics,
            after_metrics=aggregate_metrics,
            co2_projection={"before": co2_before, "after": co2_before, "energy_saved_kwh": 0.0},
            session_emissions=emissions,
            alternative_code="",
        )
        
        return jsonify(response)
    
    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid ZIP file"}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing project: {str(e)}"}), 500
    finally:
        # Cleanup
        try:
            os.remove(temp_zip_path)
        except Exception:
            pass
        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    app.run(debug=True, port=5000)
