const runDemoButton = document.getElementById("run-demo");
const downloadButton = document.getElementById("download-csv");
const demoStatus = document.getElementById("demo-status");
const summaryContainer = document.getElementById("scorecard-summary");
const sectionsContainer = document.getElementById("scorecard-sections");
const evidenceBody = document.getElementById("evidence-body");
const evidenceCount = document.getElementById("evidence-count");
const year = document.getElementById("year");

if (year) {
  year.textContent = new Date().getFullYear();
}

let currentEvidence = [];

const formatScore = (value) => {
  if (typeof value !== "number") return "-";
  return value.toFixed(1).replace(/\.0$/, "");
};

const setStatus = (message) => {
  demoStatus.textContent = message;
};

const buildSummary = (data) => {
  const { candidate, assessment, totals } = data;
  const percent = totals.max_score
    ? Math.round((totals.total_score / totals.max_score) * 100)
    : 0;

  summaryContainer.innerHTML = `
    <div class="summary-grid">
      <div class="summary-stat">
        <span class="label">Candidate</span>
        <div class="stat-value">${candidate.name}</div>
        <div class="muted">${candidate.cohort}</div>
      </div>
      <div class="summary-stat">
        <span class="label">Assessment</span>
        <div class="stat-value">${assessment.title}</div>
        <div class="muted">Version ${assessment.version}</div>
      </div>
      <div class="summary-stat">
        <span class="label">Total Score</span>
        <div class="stat-value">${formatScore(totals.total_score)} / ${formatScore(
    totals.max_score
  )}</div>
        <div class="muted">${percent}% overall</div>
      </div>
      <div class="summary-stat">
        <span class="label">Score Run</span>
        <div class="stat-value">${data.score_run_id}</div>
        <div class="muted">Generated ${new Date(data.generated_at).toLocaleString()}</div>
      </div>
    </div>
  `;
};

const buildSections = (sections) => {
  if (!sections.length) {
    sectionsContainer.innerHTML = "<p class=\"summary-empty\">No section data.</p>";
    return;
  }

  const items = sections
    .map(
      (section) => `
      <div class="section-item">
        <h4>${section.name}</h4>
        <p>${formatScore(section.score)} / ${formatScore(section.max_score)}
          &middot; ${section.notes}</p>
      </div>
    `
    )
    .join("");

  sectionsContainer.innerHTML = `
    <div class="section-list">
      ${items}
    </div>
  `;
};

const buildEvidenceTable = (evidence) => {
  if (!evidence.length) {
    evidenceBody.innerHTML = `
      <tr>
        <td colspan="5" class="table-empty">No evidence found.</td>
      </tr>
    `;
    evidenceCount.textContent = "0 items";
    return;
  }

  const rows = evidence
    .map(
      (item) => `
      <tr>
        <td><span class="label">${item.item_id}</span></td>
        <td>${item.section}</td>
        <td>${formatScore(item.score)} / ${formatScore(item.max_score)}</td>
        <td>${item.response}</td>
        <td>${item.evidence}</td>
      </tr>
    `
    )
    .join("");

  evidenceBody.innerHTML = rows;
  evidenceCount.textContent = `${evidence.length} items`;
};

const buildCsv = (evidence) => {
  const header = ["item_id", "section", "score", "max_score", "response", "evidence"];
  const sorted = [...evidence].sort((a, b) => a.item_id.localeCompare(b.item_id));

  const lines = [header.join(",")];
  for (const item of sorted) {
    const values = [
      item.item_id,
      item.section,
      formatScore(item.score),
      formatScore(item.max_score),
      item.response,
      item.evidence
    ].map((value) => `"${String(value).replace(/"/g, '""')}"`);
    lines.push(values.join(","));
  }

  return lines.join("\n");
};

const downloadCsv = () => {
  if (!currentEvidence.length) return;
  const csv = buildCsv(currentEvidence);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "scorecard-demo.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const renderScorecard = (data) => {
  buildSummary(data);
  buildSections(data.sections || []);
  currentEvidence = data.evidence || [];
  buildEvidenceTable(currentEvidence);
  downloadButton.disabled = currentEvidence.length === 0;
};

const runDemo = async () => {
  setStatus("Loading dataset...");
  runDemoButton.disabled = true;
  try {
    const response = await fetch("./data/scorecard.sample.json", {
      cache: "no-store"
    });
    if (!response.ok) {
      throw new Error("Failed to load dataset");
    }
    const data = await response.json();
    renderScorecard(data);
    setStatus("Demo loaded. Scorecard and evidence are now visible.");
  } catch (error) {
    setStatus("Unable to load demo data. Check file path and try again.");
  } finally {
    runDemoButton.disabled = false;
  }
};

runDemoButton.addEventListener("click", runDemo);
downloadButton.addEventListener("click", downloadCsv);
