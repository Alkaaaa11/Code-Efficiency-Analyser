const form = document.getElementById("analysis-form");
const resultsSection = document.getElementById("results");
const summaryCard = document.getElementById("summary-card");
const co2Card = document.getElementById("co2-card");
const beforeMetricsEl = document.getElementById("before-metrics");
const afterMetricsEl = document.getElementById("after-metrics");
const alternativeCodeEl = document.getElementById("alternative-code");

const BACKEND_URL = "http://localhost:5000/api/analyze";

const prettify = (data) => JSON.stringify(data, null, 2);

const renderSummary = (suggestion) => {
  summaryCard.innerHTML = `
    <h3>Optimization Summary</h3>
    <p>${suggestion.summary || "Model summary unavailable."}</p>
    <p class="meta">Model: ${suggestion.ai_model_used || "heuristic fallback"}</p>
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

const handleError = (message) => {
  resultsSection.hidden = false;
  summaryCard.innerHTML = `<p class="error">${message}</p>`;
  co2Card.innerHTML = "";
  beforeMetricsEl.textContent = "";
  afterMetricsEl.textContent = "";
  alternativeCodeEl.textContent = "";
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
    beforeMetricsEl.textContent = prettify(payload.analysis.before);
    afterMetricsEl.textContent = prettify(payload.analysis.after);
    alternativeCodeEl.textContent = payload.alternative_code;
    resultsSection.hidden = false;
  } catch (error) {
    handleError(error.message);
  }
});
