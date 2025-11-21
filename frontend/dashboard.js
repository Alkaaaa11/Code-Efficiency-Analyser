const dashboardTotalsCard = document.getElementById("dashboard-totals");
const dashboardReportList = document.getElementById("dashboard-report");
const refreshButton = document.getElementById("refresh-dashboard");
const co2ChartCanvas = document.getElementById("co2-chart");
const compileChartCanvas = document.getElementById("compile-chart");

const DASHBOARD_URL = "http://localhost:5000/api/dashboard";

const formatNumber = (value, digits = 2) => Number(value || 0).toFixed(digits);

let co2Chart;
let compileChart;

const upsertChart = (chart, ctx, { labels, label, data, borderColor, backgroundColor }) => {
  if (!ctx) return null;
  if (chart) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
    return chart;
  }
  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label,
          data,
          borderColor,
          backgroundColor,
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 2,
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
};

const renderDashboard = (payload = {}) => {
  const timeseries = payload.timeseries || [];
  const totals = payload.totals || {};

  dashboardTotalsCard.innerHTML = `
    <h3>Totals (Last ${totals.runs || 0} runs)</h3>
    <p>CO₂ saved: <strong>${formatNumber(totals.co2_saved_total, 4)} kg</strong></p>
    <p>Compile time saved: <strong>${formatNumber(totals.compile_time_saved_total, 2)} pts</strong></p>
    <p>Avg CO₂ saved: <strong>${formatNumber(totals.co2_saved_avg, 4)} kg</strong></p>
    <p>Avg compile savings: <strong>${formatNumber(totals.compile_time_saved_avg, 2)} pts</strong></p>
  `;

  const reportItems = payload.report || [];
  dashboardReportList.innerHTML = reportItems.length
    ? reportItems.map((item) => `<li>${item}</li>`).join("")
    : "<li>No impact report yet. Run an analysis to generate insights.</li>";

  const labels = timeseries.map((entry) =>
    new Date(entry.created_at).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  );
  const co2Data = timeseries.map((entry) => entry.co2_saved);
  const compileData = timeseries.map((entry) => entry.compile_time_saved);

  co2Chart = upsertChart(co2Chart, co2ChartCanvas?.getContext("2d"), {
    labels,
    label: "CO₂ Saved (kg)",
    data: co2Data,
    borderColor: "#6bffc5",
    backgroundColor: "rgba(107, 255, 197, 0.3)",
  });

  compileChart = upsertChart(compileChart, compileChartCanvas?.getContext("2d"), {
    labels,
    label: "Compile Time Saved (pts)",
    data: compileData,
    borderColor: "#2f8af5",
    backgroundColor: "rgba(47, 138, 245, 0.3)",
  });
};

const loadDashboard = async () => {
  try {
    refreshButton.disabled = true;
    const response = await fetch(DASHBOARD_URL);
    if (!response.ok) throw new Error("Failed to load dashboard");
    const payload = await response.json();
    renderDashboard(payload);
  } catch (error) {
    dashboardReportList.innerHTML = `<li class="error">${error.message}</li>`;
  } finally {
    refreshButton.disabled = false;
  }
};

refreshButton?.addEventListener("click", loadDashboard);

loadDashboard();

