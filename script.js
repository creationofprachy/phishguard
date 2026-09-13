const form = document.getElementById("analyzeForm");
const urlInput = document.getElementById("urlInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const errorBox = document.getElementById("errorBox");
const resultCard = document.getElementById("resultCard");
const verdictBadge = document.getElementById("verdictBadge");
const resultUrl = document.getElementById("resultUrl");
const riskScore = document.getElementById("riskScore");
const confidence = document.getElementById("confidence");
const meterFill = document.getElementById("meterFill");
const contributorsList = document.getElementById("contributorsList");
const historyBody = document.getElementById("historyBody");
const metricsGrid = document.getElementById("metricsGrid");
const modelBadge = document.getElementById("modelBadge");

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}

async function analyzeUrl(url) {
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Analysis failed.");
  }
  return data;
}

function renderResult(result) {
  resultCard.classList.remove("hidden");
  verdictBadge.textContent = result.verdict;
  verdictBadge.className = `verdict-badge verdict-${result.verdict}`;
  resultUrl.textContent = result.url;
  riskScore.textContent = `${result.risk_score}%`;
  confidence.textContent = `${result.confidence}%`;
  meterFill.style.width = `${result.risk_score}%`;

  contributorsList.innerHTML = "";
  result.top_contributors.forEach((c) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="c-name">${c.feature}</span><span class="c-value">value=${c.value} · weight=${c.importance}</span>`;
    contributorsList.appendChild(li);
  });
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const data = await res.json();
  if (!data.items || data.items.length === 0) {
    historyBody.innerHTML = '<tr><td colspan="4" class="empty-row">No URLs analyzed yet.</td></tr>';
    return;
  }
  historyBody.innerHTML = data.items
    .map((item) => {
      const time = new Date(item.analyzed_at).toLocaleTimeString();
      return `<tr>
        <td>${item.url}</td>
        <td>${item.verdict}</td>
        <td>${item.risk_score}%</td>
        <td>${time}</td>
      </tr>`;
    })
    .join("");
}

async function loadMetrics() {
  try {
    const res = await fetch("/api/metrics");
    if (!res.ok) throw new Error();
    const data = await res.json();
    modelBadge.textContent = `Model: ${data.selected_model}`;
    const rf = data.random_forest || {};
    metricsGrid.innerHTML = `
      <div class="metric-card"><div class="m-label">Accuracy</div><div class="m-value">${(rf.accuracy * 100).toFixed(1)}%</div></div>
      <div class="metric-card"><div class="m-label">Precision</div><div class="m-value">${(rf.precision * 100).toFixed(1)}%</div></div>
      <div class="metric-card"><div class="m-label">Recall</div><div class="m-value">${(rf.recall * 100).toFixed(1)}%</div></div>
      <div class="metric-card"><div class="m-label">F1 Score</div><div class="m-value">${(rf.f1_score * 100).toFixed(1)}%</div></div>
      <div class="metric-card"><div class="m-label">ROC-AUC</div><div class="m-value">${rf.roc_auc}</div></div>
      <div class="metric-card"><div class="m-label">Test Samples</div><div class="m-value">${data.n_test_samples}</div></div>
    `;
  } catch (e) {
    modelBadge.textContent = "Model: unavailable";
    metricsGrid.innerHTML = '<div class="metric-loading">Model metrics unavailable. Run training first.</div>';
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  const url = urlInput.value.trim();
  if (!url) {
    showError("Please enter a URL to analyze.");
    return;
  }
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing...";
  try {
    const result = await analyzeUrl(url);
    renderResult(result);
    await loadHistory();
  } catch (err) {
    showError(err.message);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze URL";
  }
});

clearBtn.addEventListener("click", async () => {
  await fetch("/api/history", { method: "DELETE" });
  await loadHistory();
});

loadHistory();
loadMetrics();
