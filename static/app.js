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

  syncAllPickersFromHiddenFields();
  syncCountrySelectFromHiddenField();
}

/* ---------- tag pickers: preset checkboxes + custom "Other" chips ---------- */
/* These write into the hidden <textarea>/<input> that share their field's
   real form name, so the existing FormData-based submit and the fillSetupForm
   population above never need to know this picker UI exists. */

const TAG_PRESETS = {
  on_site_cities: [
    "Karachi", "Lahore", "Islamabad", "Quetta", "Peshawar", "Faisalabad",
    "Multan", "Rawalpindi", "Dubai", "Riyadh", "Doha", "London", "New York"
  ],
  target_titles: [
    "Customer Service Representative", "Customer Support Specialist",
    "Technical Support Agent", "Virtual Assistant", "Data Entry Clerk",
    "Sales Representative", "Telesales / Telemarketing Agent",
    "Administrative Assistant", "Content Writer", "Social Media Manager",
    "Graphic Designer", "Software Developer", "Accountant",
    "HR Coordinator", "Project Manager"
  ],
  must_have_keywords: [
    "customer service", "crm", "data entry", "sales", "communication skills",
    "remote work", "ms office", "typing", "english fluency", "problem solving"
  ],
  nice_to_have_keywords: [
    "remote", "kpi", "multilingual", "night shift", "weekend availability",
    "bilingual", "flexible hours", "team player", "fast learner"
  ],
  exclude_keywords: [
    "software engineer", "devops", "night shift only", "unpaid internship",
    "commission only", "relocation required", "on-site only"
  ],
};

function tagPickerContainers() {
  return Array.from(document.querySelectorAll(".tagpicker[data-field]"));
}

function renderTagPickers() {
  tagPickerContainers().forEach((container) => {
    const field = container.dataset.field;
    const presets = TAG_PRESETS[field] || [];
    const grid = document.createElement("div");
    grid.className = "tagpicker-grid";
    presets.forEach((preset) => {
      const label = document.createElement("label");
      label.className = "tagpicker-option";
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = preset;
      input.addEventListener("change", () => syncHiddenField(field));
      label.appendChild(input);
      label.appendChild(document.createTextNode(preset));
      grid.appendChild(label);
    });

    const chips = document.createElement("div");
    chips.className = "tagpicker-chips";

    const addRow = document.createElement("div");
    addRow.className = "tagpicker-add-row";
    const addInput = document.createElement("input");
    addInput.type = "text";
    addInput.placeholder = "Add your own \u2014 press Enter";
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add";

    function addFromInput() {
      const raw = addInput.value;
      if (!raw.trim()) return;
      raw.split(/[,\n]/).map((s) => s.trim()).filter(Boolean).forEach((val) => {
        addChip(container, field, val);
      });
      addInput.value = "";
      syncHiddenField(field);
    }
    addBtn.addEventListener("click", addFromInput);
    addInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addFromInput();
      }
    });
    addRow.appendChild(addInput);
    addRow.appendChild(addBtn);

    container.appendChild(grid);
    container.appendChild(chips);
    container.appendChild(addRow);
  });
}

function addChip(container, field, value) {
  const chips = container.querySelector(".tagpicker-chips");
  // Don't add a duplicate chip, and don't add a chip for something that's
  // already one of the preset checkboxes (check the box instead).
  const presetMatch = Array.from(container.querySelectorAll(".tagpicker-option input"))
    .find((cb) => cb.value.toLowerCase() === value.toLowerCase());
  if (presetMatch) {
    presetMatch.checked = true;
    return;
  }
  const existing = Array.from(chips.querySelectorAll(".tagpicker-chip"))
    .find((el) => el.dataset.value.toLowerCase() === value.toLowerCase());
  if (existing) return;

  const chip = document.createElement("span");
  chip.className = "tagpicker-chip";
  chip.dataset.value = value;
  const label = document.createElement("span");
  label.textContent = value;
  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.textContent = "\u00d7";
  removeBtn.addEventListener("click", () => {
    chip.remove();
    syncHiddenField(field);
  });
  chip.appendChild(label);
  chip.appendChild(removeBtn);
  chips.appendChild(chip);
}

function syncHiddenField(field) {
  const container = document.querySelector(`.tagpicker[data-field="${field}"]`);
  const hidden = setupForm.elements[field];
  if (!container || !hidden) return;
  const sep = container.dataset.sep === ", " ? ", " : "\n";
  const checked = Array.from(container.querySelectorAll(".tagpicker-option input:checked")).map((cb) => cb.value);
  const chips = Array.from(container.querySelectorAll(".tagpicker-chip")).map((el) => el.dataset.value);
  hidden.value = [...checked, ...chips].join(sep);
}

function syncAllPickersFromHiddenFields() {
  tagPickerContainers().forEach((container) => {
    const field = container.dataset.field;
    const hidden = setupForm.elements[field];
    if (!hidden) return;
    // Reset UI state before repopulating from the hidden field's value.
    container.querySelectorAll(".tagpicker-option input").forEach((cb) => (cb.checked = false));
    const chipsBox = container.querySelector(".tagpicker-chips");
    if (chipsBox) chipsBox.innerHTML = "";

    const sep = container.dataset.sep === ", " ? "," : "\n";
    const values = (hidden.value || "")
      .split(sep === "," ? /,/ : /\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    values.forEach((v) => addChip(container, field, v));
  });
}

/* ---------- country select ---------- */

const COUNTRIES = [
  ["pk", "Pakistan"], ["us", "United States"], ["gb", "United Kingdom"],
  ["ca", "Canada"], ["au", "Australia"], ["ae", "United Arab Emirates"],
  ["sa", "Saudi Arabia"], ["qa", "Qatar"], ["in", "India"],
  ["bd", "Bangladesh"], ["ph", "Philippines"], ["de", "Germany"],
  ["fr", "France"], ["nl", "Netherlands"], ["ie", "Ireland"],
  ["sg", "Singapore"], ["my", "Malaysia"], ["za", "South Africa"],
  ["ng", "Nigeria"], ["ke", "Kenya"], ["eg", "Egypt"], ["tr", "Turkey"],
  ["es", "Spain"], ["it", "Italy"], ["pl", "Poland"], ["nz", "New Zealand"],
];

function renderCountrySelect() {
  const select = document.getElementById("countrySelect");
  if (!select) return;
  select.innerHTML = "";
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = "Select country\u2026";
  select.appendChild(blank);
  COUNTRIES.forEach(([code, name]) => {
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = `${name} (${code})`;
    select.appendChild(opt);
  });
  const other = document.createElement("option");
  other.value = "__other__";
  other.textContent = "Other \u2014 type below";
  select.appendChild(other);

  const otherInput = document.getElementById("countryOther");
  const hidden = document.getElementById("countryCodeValue");

  select.addEventListener("change", () => {
    if (select.value === "__other__") {
      otherInput.style.display = "";
      otherInput.focus();
      hidden.value = otherInput.value.trim().toLowerCase();
    } else {
      otherInput.style.display = "none";
      hidden.value = select.value;
    }
  });
  otherInput.addEventListener("input", () => {
    hidden.value = otherInput.value.trim().toLowerCase();
  });
}

function syncCountrySelectFromHiddenField() {
  const select = document.getElementById("countrySelect");
  const otherInput = document.getElementById("countryOther");
  const hidden = document.getElementById("countryCodeValue");
  if (!select || !hidden) return;
  const code = (hidden.value || "").trim().toLowerCase();
  const match = COUNTRIES.find(([c]) => c === code);
  if (match) {
    select.value = code;
    otherInput.style.display = "none";
  } else if (code) {
    select.value = "__other__";
    otherInput.value = code;
    otherInput.style.display = "";
  } else {
    select.value = "";
    otherInput.style.display = "none";
  }
}

renderTagPickers();
renderCountrySelect();

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
