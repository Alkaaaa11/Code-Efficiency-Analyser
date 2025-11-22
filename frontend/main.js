const form = document.getElementById("analysis-form");
const resultsSection = document.getElementById("results");
const summaryCard = document.getElementById("summary-card");
const co2Card = document.getElementById("co2-card");
const emissionsCard = document.getElementById("emissions-card");
const beforeMetricsEl = document.getElementById("before-metrics");
const afterMetricsEl = document.getElementById("after-metrics");
const alternativeCodeEl = document.getElementById("alternative-code");
const insightsList = document.getElementById("analysis-insights");
const historyPanel = document.getElementById("history-panel");
const historyBody = document.getElementById("history-body");

const BACKEND_URL = "http://localhost:5000/api/analyze";
const HISTORY_URL = "http://localhost:5000/api/history";
const PROJECT_ANALYZE_URL = "http://localhost:5000/api/analyze-project";

const prettify = (data) => JSON.stringify(data, null, 2);

// Single file upload elements
const codeFileInput = document.getElementById("code-file-input");
const codeFileInfo = document.getElementById("code-file-info");
const analyzeUploadedFileBtn = document.getElementById("analyze-uploaded-file-btn");
let uploadedCodeFile = null;
let uploadedCodeContent = null;

const renderSummary = (suggestion) => {
  summaryCard.innerHTML = `
    <h3>Optimization Summary</h3>
    <p>${suggestion.summary || "Model summary unavailable."}</p>
    <p class="meta">Model: ${suggestion.ai_model_used || "heuristic fallback"}</p>
    <p class="meta">Confidence: ${suggestion.confidence || "n/a"}</p>
  `;
};

const renderCO2 = (co2) => {
  const saving = co2.energy_saved_kwh;
  const percent = co2.before.energy_kwh
    ? ((co2.before.energy_kwh - co2.after.energy_kwh) / co2.before.energy_kwh) * 100
    : 0;
  co2Card.innerHTML = `
    <h3>CO₂ Impact</h3>
    <p>Before: <strong>${co2.before.co2_kg} kg</strong></p>
    <p>After: <strong>${co2.after.co2_kg} kg</strong></p>
    <p>Energy Saved: <strong>${saving} kWh (${percent.toFixed(1)}%)</strong></p>
  `;
};

const renderEmissions = (session) => {
  emissionsCard.innerHTML = `
    <h3>Measured Emissions</h3>
    <p>Energy Used: <strong>${session.energy_kwh?.toFixed(6) || 0} kWh</strong></p>
    <p>CO₂ Emitted: <strong>${session.co2_kg?.toFixed(6) || 0} kg</strong></p>
    <p>Duration: <strong>${session.duration_s?.toFixed(2) || 0} s</strong></p>
  `;
};

const renderInsights = (insights = []) => {
  if (!insights.length) {
    insightsList.innerHTML = "<li>No AI insights were returned.</li>";
    return;
  }
  insightsList.innerHTML = insights
    .map(
      (item) => `
      <li>
        <strong>${item.issue}</strong>
        <p>${item.impact}</p>
        <p class="meta">${item.action}</p>
      </li>
    `
    )
    .join("");
};

const renderHistory = (history = []) => {
  if (!history.length) {
    historyPanel.hidden = true;
    historyBody.innerHTML = "";
    return;
  }
  historyPanel.hidden = false;
  historyBody.innerHTML = history
    .map(
      (entry) => `
      <tr>
        <td>${entry.id}</td>
        <td>${entry.language}</td>
        <td>${entry.summary || "n/a"}</td>
        <td>${entry.ai_model || "heuristic"}</td>
        <td>${new Date(entry.created_at).toLocaleString()}</td>
      </tr>
    `
    )
    .join("");
};

const handleError = (message) => {
  resultsSection.hidden = false;
  summaryCard.innerHTML = `<p class="error">${message}</p>`;
  co2Card.innerHTML = "";
  emissionsCard.innerHTML = "";
  beforeMetricsEl.textContent = "";
  afterMetricsEl.textContent = "";
  alternativeCodeEl.textContent = "";
  insightsList.innerHTML = "";
};

const detectLanguageFromFile = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const langMap = {
    'py': 'python',
    'java': 'java',
    'js': 'javascript',
    'jsx': 'javascript',
    'html': 'html',
    'htm': 'html',
    'css': 'css'
  };
  return langMap[ext] || 'python';
};

codeFileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  uploadedCodeFile = file;
  const language = detectLanguageFromFile(file.name);
  
  // Auto-select language in dropdown
  document.getElementById("language").value = language;
  
  // Read file content
  try {
    uploadedCodeContent = await file.text();
    document.getElementById("code").value = uploadedCodeContent;
    
    codeFileInfo.style.display = "block";
    codeFileInfo.textContent = `✅ Loaded: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
    codeFileInfo.style.color = "var(--accent)";
    codeFileInfo.style.fontWeight = "600";
    
    analyzeUploadedFileBtn.style.display = "block";
  } catch (error) {
    codeFileInfo.style.display = "block";
    codeFileInfo.textContent = `❌ Error reading file: ${error.message}`;
    codeFileInfo.style.color = "#dc2626";
    analyzeUploadedFileBtn.style.display = "none";
  }
});

analyzeUploadedFileBtn.addEventListener("click", async () => {
  if (!uploadedCodeContent) {
    alert("Please upload a file first");
    return;
  }

  const language = document.getElementById("language").value;
  await analyzeCode(uploadedCodeContent, language);
});

const analyzeCode = async (code, language) => {
  // Hide project results when doing single file analysis
  projectResults.hidden = true;

  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unknown error");
    }

    renderSummary(payload.suggestion);
    renderCO2(payload.co2);
    renderEmissions(payload.session_emissions || {});
    renderInsights(payload.suggestion.analysis_insights || []);
    beforeMetricsEl.textContent = prettify(payload.analysis.before);
    afterMetricsEl.textContent = prettify(payload.analysis.after);
    alternativeCodeEl.textContent = payload.alternative_code;
    renderHistory(payload.history || []);
    resultsSection.hidden = false;
    resultsSection.scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    handleError(error.message);
  }
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = document.getElementById("code").value;
  const language = document.getElementById("language").value;

  if (!code.trim() && !uploadedCodeContent) {
    alert("Please paste code or upload a file");
    return;
  }

  const codeToAnalyze = code.trim() || uploadedCodeContent;
  await analyzeCode(codeToAnalyze, language);
});

const bootstrapHistory = async () => {
  try {
    const response = await fetch(HISTORY_URL);
    const payload = await response.json();
    renderHistory(payload.items || []);
  } catch {
    historyPanel.hidden = true;
  }
};

// Project upload functionality
const uploadArea = document.getElementById("upload-area");
const projectFileInput = document.getElementById("project-file");
const analyzeProjectBtn = document.getElementById("analyze-project-btn");
const projectUploadStatus = document.getElementById("project-upload-status");
const projectResults = document.getElementById("project-results");
let selectedFile = null;

const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
};

uploadArea.addEventListener("click", () => {
  projectFileInput.click();
});

projectFileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) {
    if (!file.name.endsWith(".zip")) {
      projectUploadStatus.style.display = "block";
      projectUploadStatus.innerHTML = '<p style="color: #dc2626;">Please select a ZIP file.</p>';
      return;
    }
    selectedFile = file;
    const fileInfo = document.getElementById("file-info");
    fileInfo.style.display = "block";
    fileInfo.textContent = `✅ Selected: ${file.name} (${formatFileSize(file.size)})`;
    fileInfo.style.color = "var(--accent)";
    fileInfo.style.fontWeight = "600";
    analyzeProjectBtn.style.display = "block";
    uploadArea.style.borderColor = "var(--accent)";
    uploadArea.style.background = "var(--accent-lightest)";
    projectUploadStatus.style.display = "none";
  }
});

uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("dragover");
  
  const file = e.dataTransfer.files[0];
  if (file && file.name.endsWith(".zip")) {
    selectedFile = file;
    projectFileInput.files = e.dataTransfer.files;
    const fileInfo = document.getElementById("file-info");
    fileInfo.style.display = "block";
    fileInfo.textContent = `✅ Selected: ${file.name} (${formatFileSize(file.size)})`;
    fileInfo.style.color = "var(--accent)";
    fileInfo.style.fontWeight = "600";
    analyzeProjectBtn.style.display = "block";
    uploadArea.style.borderColor = "var(--accent)";
    uploadArea.style.background = "var(--accent-lightest)";
    projectUploadStatus.style.display = "none";
  } else {
    projectUploadStatus.style.display = "block";
    projectUploadStatus.innerHTML = '<p style="color: #dc2626;">Please upload a ZIP file.</p>';
  }
});

const renderProjectResults = (data) => {
  const projectAnalysis = data.project_analysis;
  const summary = projectAnalysis.summary;
  
  // Summary cards
  const projectSummary = document.getElementById("project-summary");
  projectSummary.innerHTML = `
    <article class="card">
      <h3>Project Summary</h3>
      <p>Total Files: <strong>${summary.total_files}</strong></p>
      <p>Total LOC: <strong>${summary.total_lines_of_code}</strong></p>
      <p>Total Complexity: <strong>${summary.total_complexity}</strong></p>
      <p>Languages: <strong>${summary.languages.join(", ")}</strong></p>
    </article>
    <article class="card">
      <h3>CO₂ Impact</h3>
      <p>Estimated CO₂: <strong>${data.co2.before.co2_kg} kg</strong></p>
      <p>Energy: <strong>${data.co2.before.energy_kwh} kWh</strong></p>
    </article>
    <article class="card">
      <h3>Interconnections</h3>
      <p>File Dependencies: <strong>${summary.interconnection_count}</strong></p>
    </article>
  `;
  
  // Files list
  const filesList = document.getElementById("project-files-list");
  filesList.innerHTML = `
    <h4>Analyzed Files (${Object.keys(projectAnalysis.files).length})</h4>
    ${Object.entries(projectAnalysis.files).map(([path, fileData]) => `
      <div class="file-item">
        <strong>${path}</strong> (${fileData.language || "unknown"})
        ${fileData.metrics ? `
          <div class="meta">
            LOC: ${fileData.metrics.lines_of_code}, 
            Complexity: ${fileData.metrics.estimated_complexity.toFixed(2)}
          </div>
        ` : ""}
        ${fileData.error ? `<div style="color: #dc2626;">Error: ${fileData.error}</div>` : ""}
      </div>
    `).join("")}
  `;
  
  // Interconnections
  const interconnections = document.getElementById("interconnection-graph");
  if (projectAnalysis.interconnections && projectAnalysis.interconnections.length > 0) {
    interconnections.innerHTML = `
      <h4>File Interconnections</h4>
      ${projectAnalysis.interconnections.map(conn => `
        <div class="interconnection-item">
          <strong>${conn.from}</strong> → <strong>${conn.to}</strong>
          <span class="meta">(${conn.type})</span>
        </div>
      `).join("")}
    `;
  } else {
    interconnections.innerHTML = `
      <h4>File Interconnections</h4>
      <p class="meta">No interconnections detected.</p>
    `;
  }
  
  // Suggestions
  const suggestionsDiv = document.getElementById("project-suggestions");
  if (data.suggestions && data.suggestions.length > 0) {
    suggestionsDiv.innerHTML = `
      <h3>Optimization Suggestions</h3>
      ${data.suggestions.map(s => `
        <div class="card" style="margin-top: 1rem;">
          <h4>${s.file}</h4>
          <p>${s.suggestion.summary || "No summary available"}</p>
          ${s.suggestion.analysis_insights ? `
            <ul>
              ${s.suggestion.analysis_insights.map(insight => `
                <li><strong>${insight.issue}</strong>: ${insight.impact}</li>
              `).join("")}
            </ul>
          ` : ""}
        </div>
      `).join("")}
    `;
  } else {
    suggestionsDiv.innerHTML = "";
  }
  
  projectResults.hidden = false;
  projectResults.scrollIntoView({ behavior: "smooth" });
};

analyzeProjectBtn.addEventListener("click", async () => {
  if (!selectedFile) {
    projectUploadStatus.style.display = "block";
    projectUploadStatus.innerHTML = '<p style="color: #dc2626;">Please select a file first.</p>';
    return;
  }
  
  if (selectedFile.size > 250 * 1024 * 1024) {
    projectUploadStatus.style.display = "block";
    projectUploadStatus.innerHTML = '<p style="color: #dc2626;">File size exceeds 250 MB limit.</p>';
    return;
  }
  
  // Hide single file results when doing project analysis
  resultsSection.hidden = true;
  
  analyzeProjectBtn.disabled = true;
  analyzeProjectBtn.textContent = "Analyzing...";
  projectUploadStatus.style.display = "block";
  projectUploadStatus.innerHTML = '<p style="color: var(--accent);">📤 Uploading and analyzing project... This may take a moment.</p>';
  
  const formData = new FormData();
  formData.append("file", selectedFile);
  
  try {
    const response = await fetch(PROJECT_ANALYZE_URL, {
      method: "POST",
      body: formData,
    });
    
    const payload = await response.json();
    
    if (!response.ok) {
      throw new Error(payload.error || "Analysis failed");
    }
    
    projectUploadStatus.innerHTML = '<p style="color: #059669; font-weight: 600;">✅ Analysis complete!</p>';
    renderProjectResults(payload);
    
    // Refresh history
    bootstrapHistory();
  } catch (error) {
    projectUploadStatus.innerHTML = `<p style="color: #dc2626;">❌ Error: ${error.message}</p>`;
  } finally {
    analyzeProjectBtn.disabled = false;
    analyzeProjectBtn.textContent = "Analyze & Optimize Project";
  }
});

bootstrapHistory();
