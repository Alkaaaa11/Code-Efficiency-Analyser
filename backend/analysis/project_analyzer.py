"""Multi-file project analysis with interconnection detection."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .complexity import analyze_code_complexity, SUPPORTED_LANGUAGES


def detect_language_from_filename(filename: str) -> str | None:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".jsx": "javascript",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
    }
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext)


def find_imports_and_dependencies(code: str, language: str) -> Set[str]:
    """Extract import/require statements to find file dependencies."""
    dependencies: Set[str] = set()
    
    if language == "python":
        # Match: import X, from X import Y, from X.Y import Z
        patterns = [
            r"^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
            r"^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import",
        ]
    elif language == "java":
        # Match: import X.Y.Z;
        patterns = [r"^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)"]
    elif language == "javascript":
        # Match: import X from '...', require('...'), const X = require('...')
        patterns = [
            r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]",
            r"import\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
    elif language == "html":
        # Match: <script src="...">, <link href="...">
        patterns = [
            r'<script[^>]+src=["\']([^"\']+)["\']',
            r'<link[^>]+href=["\']([^"\']+)["\']',
        ]
    elif language == "css":
        # Match: @import "..."
        patterns = [r'@import\s+["\']([^"\']+)["\']']
    else:
        return dependencies
    
    for pattern in patterns:
        matches = re.findall(pattern, code, re.MULTILINE | re.IGNORECASE)
        dependencies.update(matches)
    
    return dependencies


def normalize_dependency_path(dep: str, current_file: str, project_root: str) -> str | None:
    """Normalize dependency path to a project file path."""
    # Remove query strings and fragments
    dep = dep.split("?")[0].split("#")[0]
    
    # Skip external dependencies (http, npm packages, etc.)
    if dep.startswith(("http://", "https://", "//")):
        return None
    
    # Remove leading ./ or ../
    dep = dep.lstrip("./")
    
    # Try to resolve relative to current file
    current_dir = os.path.dirname(current_file)
    if current_dir:
        potential = os.path.normpath(os.path.join(project_root, current_dir, dep))
    else:
        potential = os.path.normpath(os.path.join(project_root, dep))
    
    # Check if file exists
    if os.path.exists(potential) and os.path.isfile(potential):
        return os.path.relpath(potential, project_root)
    
    # Try direct path from project root
    potential = os.path.normpath(os.path.join(project_root, dep))
    if os.path.exists(potential) and os.path.isfile(potential):
        return os.path.relpath(potential, project_root)
    
    # Try with common extensions
    for ext in [".py", ".java", ".js", ".jsx", ".html", ".css"]:
        potential_ext = potential + ext
        if os.path.exists(potential_ext):
            return os.path.relpath(potential_ext, project_root)
    
    return None


def analyze_project(
    project_files: Dict[str, str], project_root: str = ""
) -> Dict[str, any]:
    """Analyze a multi-file project and detect interconnections."""
    
    file_analyses: Dict[str, Dict] = {}
    interconnections: List[Dict[str, str]] = []
    dependency_graph: Dict[str, Set[str]] = defaultdict(set)
    
    # First pass: analyze each file
    for filepath, content in project_files.items():
        language = detect_language_from_filename(filepath)
        if not language or language not in SUPPORTED_LANGUAGES:
            continue
        
        try:
            metrics = analyze_code_complexity(content, language)
            dependencies = find_imports_and_dependencies(content, language)
            
            file_analyses[filepath] = {
                "language": language,
                "metrics": metrics,
                "dependencies": list(dependencies),
                "lines_of_code": metrics.get("lines_of_code", 0),
            }
            
            dependency_graph[filepath] = dependencies
        except Exception as e:
            file_analyses[filepath] = {
                "language": language,
                "error": str(e),
                "metrics": {},
                "dependencies": [],
            }
    
    # Second pass: resolve interconnections
    for filepath, deps in dependency_graph.items():
        for dep in deps:
            resolved = normalize_dependency_path(dep, filepath, project_root)
            if resolved and resolved in file_analyses:
                interconnections.append({
                    "from": filepath,
                    "to": resolved,
                    "type": "import" if file_analyses[filepath]["language"] in ["python", "java", "javascript"] else "reference",
                })
    
    # Aggregate statistics
    total_files = len(file_analyses)
    total_loc = sum(f.get("lines_of_code", 0) for f in file_analyses.values())
    total_complexity = sum(f.get("metrics", {}).get("estimated_complexity", 0) for f in file_analyses.values())
    languages_used = set(f.get("language") for f in file_analyses.values() if f.get("language"))
    
    return {
        "files": file_analyses,
        "interconnections": interconnections,
        "summary": {
            "total_files": total_files,
            "total_lines_of_code": total_loc,
            "total_complexity": round(total_complexity, 2),
            "languages": list(languages_used),
            "interconnection_count": len(interconnections),
        },
    }

