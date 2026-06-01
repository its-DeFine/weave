const stageOrder = [
  "intent",
  "research",
  "selection",
  "plan",
  "engineering",
  "qa",
  "kpi",
  "marketing",
];

const loopOrder = ["iteration", "analysis"];

const controls = {
  runtimeName: document.querySelector("[data-runtime-name]"),
  reviewCount: document.querySelector("[data-review-count]"),
  healthState: document.querySelector("[data-health-state]"),
  footerVersion: document.querySelector("[data-footer-version]"),
  searchInput: document.querySelector("[data-search-input]"),
  createButtons: document.querySelectorAll("[data-toggle-create]"),
  createForm: document.querySelector("[data-create-form]"),
  createName: document.querySelector("[data-create-name]"),
  createIntent: document.querySelector("[data-create-intent]"),
  appList: document.querySelector("[data-app-list]"),
  appNameShort: document.querySelector("[data-app-name-short]"),
  appName: document.querySelector("[data-app-name]"),
  appStatus: document.querySelector("[data-app-status]"),
  metaRuntime: document.querySelector("[data-meta-runtime]"),
  metaMode: document.querySelector("[data-meta-mode]"),
  metaOwner: document.querySelector("[data-meta-owner]"),
  metaVersion: document.querySelector("[data-meta-version]"),
  stageTrack: document.querySelector("[data-stage-track]"),
  iterationLoop: document.querySelector("[data-iteration-loop]"),
  currentStageIcon: document.querySelector("[data-current-stage-icon]"),
  currentTask: document.querySelector("[data-current-task]"),
  currentSummary: document.querySelector("[data-current-summary]"),
  blockerMap: document.querySelector("[data-blocker-map]"),
  workCards: {
    plan: document.querySelector("[data-work-card='plan']"),
    review: document.querySelector("[data-work-card='review']"),
    execute: document.querySelector("[data-work-card='execute']"),
  },
  evidenceList: document.querySelector("[data-evidence-list]"),
  decisionList: document.querySelector("[data-decision-list]"),
  kpiList: document.querySelector("[data-kpi-list]"),
  eventList: document.querySelector("[data-event-list]"),
  foundationStatus: document.querySelector("[data-foundation-status]"),
  foundationList: document.querySelector("[data-foundation-list]"),
  changeList: document.querySelector("[data-change-list]"),
  apiHealthList: document.querySelector("[data-api-health-list]"),
  transcriptSummary: document.querySelector("[data-transcript-summary]"),
  runtimeWindowRoute: document.querySelector("[data-runtime-window-route]"),
  refresh: document.querySelector("[data-refresh]"),
};

let runtime = null;
let selectedAppId = null;

await loadRuntime();
wireEvents();
render();

async function loadRuntime() {
  const response = await fetch("./sample-runtime.json", { cache: "no-store" });
  runtime = await response.json();
  selectedAppId = selectedAppId ?? runtime.apps[0]?.id ?? null;
}

function wireEvents() {
  controls.createButtons.forEach((button) => {
    button.addEventListener("click", () => {
      controls.createForm.hidden = !controls.createForm.hidden;
      if (!controls.createForm.hidden) controls.createName.focus();
    });
  });

  controls.createForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const name = controls.createName.value.trim();
    const intent = controls.createIntent.value.trim();
    if (!name || !intent) return;
    const app = createDraftApp(name, intent);
    runtime.apps.push(app);
    selectedAppId = app.id;
    controls.createName.value = "";
    controls.createIntent.value = "";
    controls.createForm.hidden = true;
    render();
  });

  controls.searchInput.addEventListener("input", render);
  controls.refresh.addEventListener("click", async () => {
    await loadRuntime();
    render();
  });
}

function render() {
  const app = selectedApp();
  if (!app) return;
  const version = runtime.runtime.releaseVersion;
  const openDecisionCount = app.decisions.filter((decision) => decision.status !== "accepted").length;

  controls.runtimeName.textContent = `${runtime.runtime.name} - ${runtime.runtime.mode}`;
  controls.reviewCount.textContent = `${openDecisionCount} open`;
  controls.healthState.textContent = runtime.runtime.externalRuntimeBoundary;
  controls.footerVersion.textContent = `WEAVE ${version}`;
  controls.runtimeWindowRoute.textContent = runtime.runtime.bridgeLabel;
  controls.appNameShort.textContent = app.name;
  controls.appName.textContent = app.name;
  controls.appStatus.textContent = app.status;
  controls.appStatus.dataset.tone = app.tone;
  controls.metaRuntime.textContent = app.runtime;
  controls.metaMode.textContent = runtime.runtime.mode;
  controls.metaOwner.textContent = app.owner;
  controls.metaVersion.textContent = version;
  controls.currentStageIcon.textContent = shortStage(app.currentStage);
  controls.currentTask.textContent = app.task;
  controls.currentSummary.textContent = app.summary;
  controls.foundationStatus.textContent = app.foundationGate.passed ? "complete" : "blocked";
  controls.foundationStatus.dataset.tone = app.foundationGate.passed ? "done" : "blocked";
  controls.transcriptSummary.textContent = app.transcriptSummary;

  controls.appList.innerHTML = filteredApps().map(renderAppCard).join("");
  controls.stageTrack.innerHTML = stageOrder.map((stageId) => renderStage(app, stageId)).join("");
  controls.iterationLoop.innerHTML = renderIterationLoop(app);
  controls.blockerMap.hidden = !app.blocker;
  controls.blockerMap.innerHTML = app.blocker ? renderBlocker(app) : "";
  Object.entries(controls.workCards).forEach(([kind, element]) => {
    element.innerHTML = renderWorkCard(app.workCards.find((card) => card.id === kind));
  });
  controls.evidenceList.innerHTML = app.evidence.map(renderEvidence).join("");
  controls.decisionList.innerHTML = app.decisions.map(renderDecision).join("");
  controls.kpiList.innerHTML = app.kpis.map(renderKpi).join("");
  controls.eventList.innerHTML = app.events.map(renderEvent).join("");
  controls.foundationList.innerHTML = renderFoundation(app.foundationGate);
  controls.changeList.innerHTML = app.changes.map(renderChange).join("");
  controls.apiHealthList.innerHTML = app.restHealth.map(renderHealth).join("");

  controls.appList.querySelectorAll("[data-app-id]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedAppId = button.getAttribute("data-app-id");
      render();
    });
  });
}

function filteredApps() {
  const query = controls.searchInput.value.trim().toLowerCase();
  if (!query) return runtime.apps;
  return runtime.apps.filter((app) => {
    const haystack = [
      app.name,
      app.status,
      app.summary,
      app.task,
      app.owner,
      app.currentStage,
      app.foundationGate?.passed ? "foundation complete" : "foundation blocked",
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  });
}

function selectedApp() {
  return runtime.apps.find((app) => app.id === selectedAppId) ?? runtime.apps[0];
}

function createDraftApp(name, intent) {
  const id = slugify(name);
  return {
    id,
    name,
    status: "Draft intent",
    tone: "draft",
    currentStage: "intent",
    summary: intent,
    task: "Write the intent contract and foundation context",
    owner: "WEAVE operator",
    runtime: runtime.runtime.name,
    stages: stageOrder.map((stage, index) => ({
      id: stage,
      name: labelForStage(stage),
      state: index === 0 ? "current" : "next",
      summary: index === 0 ? intent : "Pending",
    })),
    iterationLoop: loopOrder.map((phase) => ({
      id: phase,
      name: labelForStage(phase),
      state: "next",
      summary: "Starts after KPI setup and marketing launch",
    })),
    blocker: {
      stage: "intent",
      title: "Foundation context needed",
      reason: "The app exists as a draft until owner, app, inventory, contract, lifecycle, capabilities, and blockers are recorded.",
      waitingOn: "Telegram foundation interview",
      nextAction: "Hermes asks through Telegram; the UI only displays the resulting state.",
    },
    foundationGate: {
      passed: false,
      missing: [],
      incomplete: ["soul.md", "owner-profile.md", "context/app-context.md", "inventory/app-inventory.md", "contract/gestaltian-contract.md"],
      nextAction: "Hermes must ask through Telegram before serious app work.",
    },
    workCards: [
      { id: "plan", title: "A. Plan", done: 1, total: 4, items: ["Create app room", "Fill app context", "List approval gates", "Set done criteria"] },
      { id: "review", title: "B. Review", done: 0, total: 3, items: ["Owner profile", "Contract review", "Evidence path"] },
      { id: "execute", title: "C. Execute", done: 0, total: 3, items: ["Record ledger", "Derive stage", "Run checks"] },
    ],
    evidence: [
      { label: "Lifecycle contract", path: "docs/weave-runtime-technical-gestalt-contract-v0.1.md", scope: "public", stage: "Intent" },
    ],
    decisions: [
      { label: "Admit app to lifecycle", status: "owner_required", evidence: "foundation gate", note: "Draft app needs foundation completion before Research." },
    ],
    kpis: [
      { label: "Foundation", value: "blocked", delta: "templates incomplete" },
      { label: "Public reporting", value: "not started", delta: "pending" },
    ],
    events: [
      { type: "app.created", status: "Recorded", stage: "intent", summary: "Draft app created in local UI sample only." },
    ],
    changes: [
      { type: "app", label: "Draft app added", detail: "Local sample state only", stage: "intent" },
    ],
    restHealth: [
      { label: "Health", value: "sample", detail: "No runtime write performed" },
      { label: "Auth", value: "not connected", detail: "UI is static sample data" },
    ],
    transcriptSummary: "No UI communication. Hermes communication happens through the configured external channel.",
  };
}

function renderAppCard(app) {
  const selected = app.id === selectedAppId ? "true" : "false";
  const dots = app.stages.map((stage) => `<span data-state="${escapeAttr(stage.state)}"></span>`).join("");
  return `
    <button class="app-card" type="button" data-app-id="${escapeAttr(app.id)}" aria-selected="${selected}">
      <span class="app-card-head">
        <strong>${escapeHtml(app.name)}</strong>
        <small data-tone="${escapeAttr(app.tone)}">${escapeHtml(app.status)}</small>
      </span>
      <span class="dot-row">${dots}</span>
      <small>${escapeHtml(app.summary)}</small>
    </button>
  `;
}

function renderStage(app, stageId) {
  const stage = app.stages.find((item) => item.id === stageId) ?? {
    id: stageId,
    name: labelForStage(stageId),
    state: "next",
    summary: "Pending",
  };
  return `
    <li data-state="${escapeAttr(stage.state)}" data-stage-id="${escapeAttr(stageId)}">
      <strong>${escapeHtml(stage.name)}</strong>
      <span>${escapeHtml(stage.summary)}</span>
    </li>
  `;
}

function renderIterationLoop(app) {
  const phases = app.iterationLoop ?? loopOrder.map((phase) => ({
    id: phase,
    name: labelForStage(phase),
    state: "next",
    summary: "Pending",
  }));
  const items = phases.map((phase) => `
    <li data-state="${escapeAttr(phase.state)}" data-loop-id="${escapeAttr(phase.id)}">
      <strong>${escapeHtml(phase.name)}</strong>
      <span>${escapeHtml(phase.summary)}</span>
    </li>
  `).join("");
  return `
    <div class="loop-connector" aria-hidden="true"></div>
    <div class="loop-header">
      <p class="eyebrow">Parallel growth loop</p>
      <h2>Iteration and analysis run while Marketing is live</h2>
      <span>Build improvements, read usage and feedback, then feed the next implementation pass.</span>
    </div>
    <ol class="loop-rail" aria-label="iteration and analysis loop">${items}</ol>
  `;
}

function renderBlocker(app) {
  const blocker = app.blocker;
  return `
    <div>
      <p class="eyebrow">Active blocker</p>
      <h2>${escapeHtml(blocker.title)}</h2>
      <p>${escapeHtml(blocker.reason)}</p>
    </div>
    <dl>
      <div><dt>Waiting on</dt><dd>${escapeHtml(blocker.waitingOn)}</dd></div>
      <div><dt>Next action</dt><dd>${escapeHtml(blocker.nextAction)}</dd></div>
    </dl>
  `;
}

function renderWorkCard(card) {
  if (!card) return "";
  const items = card.items.map((item, index) => {
    const done = index < card.done;
    return `<li data-done="${done}">${escapeHtml(item)}</li>`;
  }).join("");
  return `
    <div class="work-card-head">
      <h2>${escapeHtml(card.title)}</h2>
      <strong>${card.done}/${card.total}</strong>
    </div>
    <ol>${items}</ol>
  `;
}

function renderEvidence(item) {
  return `
    <li>
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.path)}</strong>
      <em>${escapeHtml(item.stage)} - ${escapeHtml(item.scope)}</em>
    </li>
  `;
}

function renderDecision(item) {
  return `
    <li data-status="${escapeAttr(item.status)}">
      <span>${escapeHtml(item.status.replaceAll("_", " "))}</span>
      <strong>${escapeHtml(item.label)}</strong>
      <p>${escapeHtml(item.note)}</p>
      <em>${escapeHtml(item.evidence)}</em>
    </li>
  `;
}

function renderKpi(item) {
  return `<li><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong><em>${escapeHtml(item.delta)}</em></li>`;
}

function renderEvent(item) {
  return `<li><span>${escapeHtml(item.status)}</span><strong>${escapeHtml(item.type)}</strong><em>${escapeHtml(item.stage)}</em><p>${escapeHtml(item.summary)}</p></li>`;
}

function renderFoundation(gate) {
  const missing = gate.missing.length ? gate.missing : ["none"];
  const incomplete = gate.incomplete.length ? gate.incomplete : ["none"];
  return `
    <li><span>Missing</span><strong>${missing.map(escapeHtml).join(", ")}</strong></li>
    <li><span>Incomplete</span><strong>${incomplete.map(escapeHtml).join(", ")}</strong></li>
    <li><span>Next</span><strong>${escapeHtml(gate.nextAction)}</strong></li>
  `;
}

function renderChange(item) {
  return `<li><span>${escapeHtml(item.type)}</span><strong>${escapeHtml(item.label)}</strong><em>${escapeHtml(item.stage)}</em><p>${escapeHtml(item.detail)}</p></li>`;
}

function renderHealth(item) {
  return `<li><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong><em>${escapeHtml(item.detail)}</em></li>`;
}

function labelForStage(stageId) {
  const labels = {
    intent: "Intent",
    research: "Research",
    selection: "Selection",
    plan: "Plan",
    engineering: "Engineering",
    qa: "QA",
    kpi: "KPI Setup",
    marketing: "Marketing",
    iteration: "Iteration",
    analysis: "Analysis",
  };
  return labels[stageId] ?? stageId;
}

function shortStage(stageId) {
  if (stageId === "engineering") return "ENG";
  if (stageId === "selection") return "SEL";
  if (stageId === "marketing") return "MKT";
  if (stageId === "iteration") return "ITR";
  if (stageId === "analysis") return "ANL";
  return labelForStage(stageId).slice(0, 3).toUpperCase();
}

function slugify(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "draft-app";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
