const runBtn = document.getElementById("runBtn");
const liveCheck = document.getElementById("liveCheck");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const matchesBoard = document.getElementById("matchesBoard");
const matchesEmpty = document.getElementById("matchesEmpty");
const linksSection = document.getElementById("linksSection");
const linkGroups = document.getElementById("linkGroups");
const historyStrip = document.getElementById("historyStrip");
const drawer = document.getElementById("drawer");
const drawerClose = document.getElementById("drawerClose");
const drawerTitle = document.getElementById("drawerTitle");
const drawerMeta = document.getElementById("drawerMeta");
const drawerNote = document.getElementById("drawerNote");

const setupBtn = document.getElementById("setupBtn");
const setupBtn2 = document.getElementById("setupBtn2");
const setupOverlay = document.getElementById("setupOverlay");
const setupClose = document.getElementById("setupClose");
const setupForm = document.getElementById("setupForm");
const setupError = document.getElementById("setupError");
const resumeCurrent = document.getElementById("resumeCurrent");

let setupComplete = false;
let pollTimer = null;

function tickClock() {
  const now = new Date();
  document.getElementById("clock").textContent =
    now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
tickClock();
setInterval(tickClock, 15000);

/* ---------- setup wizard ---------- */

function openSetup() {
  setupOverlay.classList.add("open");
}
function closeSetup() {
  setupOverlay.classList.remove("open");
  setupError.textContent = "";
}
setupBtn.addEventListener("click", openSetup);
if (setupBtn2) setupBtn2.addEventListener("click", openSetup);

// Fallback: visiting the dashboard with ?setup=1 in the address bar always
// opens the Passenger details form directly, regardless of any button.
if (new URLSearchParams(window.location.search).has("setup")) {
  openSetup();
}
setupClose.addEventListener("click", closeSetup);

function fillSetupForm(config) {
  const c = config.candidate || {};
  const s = config.search || {};
  setupForm.name.value = c.name || "";
  setupForm.email.value = c.email || "";
  setupForm.phone.value = c.phone || "";
  setupForm.current_location.value = c.current_location || "";
  setupForm.key_strengths.value = (c.key_strengths || []).join("\n");
  setupForm.on_site_cities.value = (s.on_site_cities || []).join(", ");
  setupForm.country_code.value = s.country_code || "";
  setupForm.include_remote.checked = s.include_remote !== false;
  setupForm.target_titles.value = (config.target_titles || []).join("\n");
  setupForm.must_have_keywords.value = (config.must_have_keywords || []).join("\n");
  setupForm.nice_to_have_keywords.value = (config.nice_to_have_keywords || []).join("\n");
  setupForm.exclude_keywords.value = (config.exclude_keywords || []).join("\n");
  setupForm.languages.value = (config.languages || []).join(", ");
  setupForm.min_match_score_to_report.value = config.min_match_score_to_report ?? 35;
  setupForm.min_match_score_to_auto_apply.value = config.min_match_score_to_auto_apply ?? 65;

  if (c.resume_path) {
    const name = c.resume_path.split(/[\\/]/).pop();
    resumeCurrent.textContent = `\u2014 current: ${name} (upload a new file only if you want to replace it)`;
  } else {
    resumeCurrent.textContent = "\u2014 no resume uploaded yet";
  }
}

async function loadSetup(openIfIncomplete) {
  const res = await fetch("/api/setup");
  const data = await res.json();
  setupComplete = data.complete;
  fillSetupForm(data.config);
  if (openIfIncomplete && !setupComplete) {
    openSetup();
  }
  return data;
}

setupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setupError.textContent = "";
  const fd = new FormData(setupForm);
  const res = await fetch("/api/setup", { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    setupError.textContent = data.reason || "Couldn't save — check the required fields.";
    return;
  }
  setupComplete = data.complete;
  closeSetup();
  await loadSetup(false);
});

/* ---------- run / status / results ---------- */

function prettySource(source) {
  if (!source) return "";
  const base = source.split("/")[0];
  return base.replace(/_/g, " ");
}

function applyStatusLog(job, applyLog) {
  const hit = applyLog.find(a => a.job === job.title && a.company === job.company);
  if (!hit) return null;
  return hit;
}

function statusPillFor(job, applyLog) {
  const hit = applyStatusLog(job, applyLog);
  if (!hit) return { label: "matched", cls: "status-matched" };
  const map = {
    submitted: { label: "submitted", cls: "status-submitted" },
    dry_run_filled: { label: "filled", cls: "status-filled" },
    needs_manual_review: { label: "needs review", cls: "status-review" },
    failed: { label: "failed", cls: "status-review" },
    skipped: { label: "skipped", cls: "status-skipped" },
  };
  return map[hit.status] || { label: hit.status, cls: "status-matched" };
}

function renderReport(report) {
  document.getElementById("statFetched").textContent = report.fetched_count ?? "—";
  document.getElementById("statMatched").textContent = (report.matched_jobs || []).length;
  document.getElementById("statApplied").textContent = (report.auto_apply_log || []).length;
  document.getElementById("statLinks").textContent = (report.manual_search_links || []).length;

  const rows = matchesBoard.querySelectorAll(".board-row-item");
  rows.forEach(r => r.remove());

  const jobs = report.matched_jobs || [];
  if (jobs.length === 0) {
    matchesEmpty.style.display = "block";
  } else {
    matchesEmpty.style.display = "none";
    jobs.forEach((job) => {
      const pill = statusPillFor(job, report.auto_apply_log || []);
      const row = document.createElement("div");
      row.className = "board-row board-row-item";
      row.innerHTML = `
        <span class="col-gate">G-${job.score}</span>
        <span class="col-dest">${escapeHtml(job.title || "Untitled")}</span>
        <span class="col-carrier">${escapeHtml(job.company || "—")}</span>
        <span class="col-src" title="${escapeHtml(job.source || "")}">${escapeHtml(prettySource(job.source))}</span>
        <span class="col-status"><span class="status-pill ${pill.cls}">${pill.label}</span></span>
      `;
      row.addEventListener("click", () => openDrawer(job));
      matchesBoard.appendChild(row);
    });
  }

  const links = report.manual_search_links || [];
  if (links.length) {
    linksSection.style.display = "block";
    const bySite = {};
    links.forEach(l => {
      bySite[l.site] = bySite[l.site] || [];
      bySite[l.site].push(l);
    });
    linkGroups.innerHTML = "";
    Object.entries(bySite).forEach(([site, items]) => {
      const group = document.createElement("div");
      group.className = "link-group";
      group.innerHTML = `<h3>${escapeHtml(site)}</h3>`;
      items.forEach(l => {
        const row = document.createElement("div");
        row.className = "link-row";
        row.innerHTML = `<span>${escapeHtml(l.query)}</span><a href="${l.url}" target="_blank" rel="noopener">open \u2197</a>`;
        group.appendChild(row);
      });
      linkGroups.appendChild(group);
    });
  } else {
    linksSection.style.display = "none";
  }
}

function openDrawer(job) {
  drawerTitle.textContent = job.title || "Untitled role";
  drawerMeta.textContent = `${job.company || "Unknown company"} \u2014 gate G-${job.score} \u2014 ${job.source || ""}`;
  drawerNote.textContent = job.cover_note || "No cover note drafted for this listing.";
  drawer.classList.add("open");
}
drawerClose.addEventListener("click", () => drawer.classList.remove("open"));

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function setStatus(state) {
  statusDot.classList.remove("running", "done", "error");
  if (state.status === "running") {
    statusDot.classList.add("running");
    statusText.textContent = state.step || "Running\u2026";
    runBtn.disabled = true;
    runBtn.textContent = "Running\u2026";
  } else if (state.status === "done") {
    statusDot.classList.add("done");
    statusText.textContent = "Done \u2014 " + new Date(state.finished_at).toLocaleTimeString();
    runBtn.disabled = false;
    runBtn.textContent = "Run search";
  } else if (state.status === "error") {
    statusDot.classList.add("error");
    statusText.textContent = "Error: " + (state.error || "unknown");
    runBtn.disabled = false;
    runBtn.textContent = "Run search";
  } else {
    statusText.textContent = "Idle \u2014 no run yet today";
    runBtn.disabled = false;
    runBtn.textContent = "Run search";
  }
}

async function poll() {
  const res = await fetch("/api/status");
  const state = await res.json();
  setStatus(state);
  if (state.status === "done" && state.result) {
    renderReport(state.result);
    loadHistory();
  }
  if (state.status === "running") {
    pollTimer = setTimeout(poll, 1200);
  }
}

runBtn.addEventListener("click", async () => {
  await loadSetup(false);
  if (!setupComplete) {
    setupError.textContent = "Fill in your name, email, and resume before running a search.";
    openSetup();
    return;
  }
  runBtn.disabled = true;
  runBtn.textContent = "Starting\u2026";
  const res = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ live: liveCheck.checked }),
  });
  if (!res.ok) {
    runBtn.disabled = false;
    runBtn.textContent = "Run search";
    return;
  }
  poll();
});

async function loadHistory() {
  const res = await fetch("/api/reports");
  const dates = await res.json();
  if (!dates.length) return;
  historyStrip.innerHTML = "";
  dates.forEach(date => {
    const chip = document.createElement("span");
    chip.className = "history-chip";
    chip.textContent = date;
    chip.addEventListener("click", async () => {
      const r = await fetch(`/api/reports/${date}`);
      const report = await r.json();
      renderReport(report);
    });
    historyStrip.appendChild(chip);
  });
}

(async function init() {
  await loadSetup(true);
  await loadHistory();
  const res = await fetch("/api/reports");
  const dates = await res.json();
  if (dates.length) {
    const r = await fetch(`/api/reports/${dates[0]}`);
    const report = await r.json();
    renderReport(report);
  }
  poll();
})();
