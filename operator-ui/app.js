const stageOrder = [
  "intent",
  "research",
  "selection",
  "plan",
  "engineering",
  "qa",
  "kpi",
  "marketing",
  "iteration",
];

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
  commandList: document.querySelector("[data-command-list]"),
  chatLog: document.querySelector("[data-chat-log]"),
  agentRoute: document.querySelector("[data-agent-route]"),
  messageForm: document.querySelector("[data-message-form]"),
  messageText: document.querySelector("[data-message-text]"),
  messageMode: document.querySelector("[data-message-mode]"),
  commandPreview: document.querySelector("[data-command-preview]"),
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

  controls.messageForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const app = selectedApp();
    const text = controls.messageText.value.trim();
    if (!text || !app) return;
    const mode = controls.messageMode.value;
    const command = buildCommandDraft(app, text, mode);
    app.chat.push({
      role: "user",
      label: "Operator draft",
      text,
      time: "now",
    });
    app.chat.push({
      role: "agent",
      label: "WEAVE Runtime",
      text: `Drafted ${command.command_type} for ${app.currentStage}. Review the command preview before any runtime write.`,
      time: "now",
    });
    app.commands.unshift({
      id: command.command_id,
      title: command.command_type,
      status: command.requires_owner_approval ? "Owner review" : "Draft",
      stage: app.currentStage,
    });
    controls.commandPreview.textContent = JSON.stringify(command, null, 2);
    controls.messageText.value = "";
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
  controls.agentRoute.textContent = runtime.runtime.bridgeLabel;
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

  controls.appList.innerHTML = filteredApps().map(renderAppCard).join("");
  controls.stageTrack.innerHTML = stageOrder.map((stageId) => renderStage(app, stageId)).join("");
  controls.blockerMap.hidden = !app.blocker;
  controls.blockerMap.innerHTML = app.blocker ? renderBlocker(app) : "";
  Object.entries(controls.workCards).forEach(([kind, element]) => {
    element.innerHTML = renderWorkCard(app.workCards.find((card) => card.id === kind));
  });
  controls.evidenceList.innerHTML = app.evidence.map(renderEvidence).join("");
  controls.decisionList.innerHTML = app.decisions.map(renderDecision).join("");
  controls.kpiList.innerHTML = app.kpis.map(renderKpi).join("");
  controls.commandList.innerHTML = app.commands.map(renderCommand).join("");
  controls.chatLog.innerHTML = app.chat.map(renderChat).join("");

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
    const haystack = [app.name, app.status, app.summary, app.task, app.owner].join(" ").toLowerCase();
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
    task: "Write the intent contract and approval boundary",
    owner: "WEAVE operator",
    runtime: runtime.runtime.name,
    stages: stageOrder.map((stage, index) => ({
      id: stage,
      name: labelForStage(stage),
      state: index === 0 ? "current" : "next",
      summary: index === 0 ? intent : "Pending",
    })),
    blocker: {
      stage: "intent",
      title: "Intent contract needed",
      reason: "The app exists as a draft until the target user, use case, constraints, and approval gates are recorded.",
      waitingOn: "Operator intent review",
      nextAction: "Ask the runtime for an intent packet.",
    },
    workCards: [
      { id: "plan", title: "A. Plan", done: 1, total: 4, items: ["Name target user", "Define constraints", "List approval gates", "Set done criteria"] },
      { id: "review", title: "B. Review", done: 0, total: 3, items: ["Owner review", "Evidence path", "Claim limits"] },
      { id: "execute", title: "C. Execute", done: 0, total: 3, items: ["Create tasks", "Run checks", "Record evidence"] },
    ],
    evidence: [
      { label: "Lifecycle contract", path: "docs/month1/weave-lifecycle-contract-v0.md", scope: "public", stage: "Intent" },
      { label: "Agent contract", path: "docs/month1/weave-agent-operating-contract-v0.md", scope: "public", stage: "Intent" },
    ],
    decisions: [
      { label: "Admit app to lifecycle", status: "owner_required", evidence: "operator-ui draft", note: "Draft app needs owner review before Research." },
    ],
    kpis: [
      { label: "KPI setup", value: "not started", delta: "blocked by Intent" },
      { label: "Public reporting", value: "not started", delta: "pending" },
    ],
    commands: [
      { id: "draft-intent", title: "brief_stage_context", status: "Draft", stage: "intent" },
    ],
    chat: [
      { role: "agent", label: "WEAVE Runtime", text: "Draft app created locally. No runtime write has been performed.", time: "now" },
    ],
  };
}

function buildCommandDraft(app, text, mode) {
  const requiresApproval = app.currentStage === "marketing" || mode === "execute";
  return {
    schema: "weave-agent-command-draft/v0.1",
    release_version: runtime.runtime.releaseVersion,
    target_app_id: app.id,
    target_app_name: app.name,
    lifecycle_stage: app.currentStage,
    command_type: commandTypeFor(mode, app.currentStage),
    operator_message: text,
    requires_owner_approval: requiresApproval,
    secret_payload_allowed: false,
    persistence: "local_preview_only",
    public_safe: true,
  };
}

function commandTypeFor(mode, stage) {
  if (stage === "marketing" || mode === "execute") return "request_owner_approval";
  if (mode === "review") return "record_decision";
  return "brief_stage_context";
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

function renderCommand(item) {
  return `<li><span>${escapeHtml(item.status)}</span><strong>${escapeHtml(item.title)}</strong><em>${escapeHtml(item.stage)}</em></li>`;
}

function renderChat(item) {
  return `
    <li data-role="${escapeAttr(item.role)}">
      <span>${escapeHtml(item.label ?? item.role)} - ${escapeHtml(item.time)}</span>
      <p>${escapeHtml(item.text)}</p>
    </li>
  `;
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
  };
  return labels[stageId] ?? stageId;
}

function shortStage(stageId) {
  if (stageId === "engineering") return "ENG";
  if (stageId === "selection") return "SEL";
  if (stageId === "marketing") return "MKT";
  if (stageId === "iteration") return "ITR";
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
