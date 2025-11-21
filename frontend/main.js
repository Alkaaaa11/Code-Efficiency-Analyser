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

const prettify = (data) => JSON.stringify(data, null, 2);

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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = document.getElementById("code").value;
  const language = document.getElementById("language").value;

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
  } catch (error) {
    handleError(error.message);
  }
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

bootstrapHistory();
