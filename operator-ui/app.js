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
  appCount: document.querySelector("[data-app-count]"),
  appList: document.querySelector("[data-app-list]"),
  appName: document.querySelector("[data-app-name]"),
  appStatus: document.querySelector("[data-app-status]"),
  stageTrack: document.querySelector("[data-stage-track]"),
  blockerTitle: document.querySelector("[data-blocker-title]"),
  blockerBody: document.querySelector("[data-blocker-body]"),
  blockerWaiting: document.querySelector("[data-blocker-waiting]"),
  blockerNext: document.querySelector("[data-blocker-next]"),
  kpis: document.querySelector("[data-kpis]"),
  evidence: document.querySelector("[data-evidence]"),
  messages: document.querySelector("[data-messages]"),
  messageForm: document.querySelector("[data-message-form]"),
  messageText: document.querySelector("[data-message-text]"),
  commandPreview: document.querySelector("[data-command-preview]"),
};

let runtime = null;
let selectedAppId = null;

const response = await fetch("./sample-runtime.json", { cache: "no-store" });
runtime = await response.json();
selectedAppId = runtime.apps[0]?.id ?? null;

controls.messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const app = selectedApp();
  const text = controls.messageText.value.trim();
  if (!text || !app) return;
  const command = {
    schema: "weave-agent-command-draft/v0.1",
    target_app_id: app.id,
    lifecycle_stage: app.currentStage,
    command_type: app.currentStage === "marketing" ? "request_owner_approval" : "brief_stage_context",
    operator_message: text,
    requires_owner_approval: app.currentStage === "marketing",
    secret_payload_allowed: false,
  };
  app.messages.push({ sender: "Operator draft", text });
  controls.commandPreview.textContent = JSON.stringify(command, null, 2);
  controls.messageText.value = "";
  render();
});

render();

function render() {
  const app = selectedApp();
  if (!app) return;

  controls.runtimeName.textContent = `${runtime.runtime.name} · ${runtime.runtime.mode}`;
  controls.appCount.textContent = `${runtime.apps.length} app`;
  controls.appList.innerHTML = runtime.apps.map(renderAppCard).join("");
  controls.appName.textContent = app.name;
  controls.appStatus.textContent = app.status;
  controls.stageTrack.innerHTML = stageOrder.map((stageId) => renderStage(app, stageId)).join("");
  controls.blockerTitle.textContent = app.blocker.title;
  controls.blockerBody.textContent = app.blocker.body;
  controls.blockerWaiting.textContent = app.blocker.waitingOn;
  controls.blockerNext.textContent = app.blocker.nextAction;
  controls.kpis.innerHTML = app.kpis.map(renderKeyValue).join("");
  controls.evidence.innerHTML = app.evidence.map(renderEvidence).join("");
  controls.messages.innerHTML = app.messages.map(renderMessage).join("");

  controls.appList.querySelectorAll("[data-app-id]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedAppId = button.getAttribute("data-app-id");
      render();
    });
  });
}

function selectedApp() {
  return runtime.apps.find((app) => app.id === selectedAppId) ?? runtime.apps[0];
}

function renderAppCard(app) {
  const selected = app.id === selectedAppId ? "true" : "false";
  const dots = app.stages
    .map((stage) => `<span data-state="${escapeAttr(stage.state)}"></span>`)
    .join("");
  return `
    <button class="app-card" type="button" data-app-id="${escapeAttr(app.id)}" aria-selected="${selected}">
      <header>
        <strong>${escapeHtml(app.name)}</strong>
        <small>${escapeHtml(app.status)}</small>
      </header>
      <span class="dot-row">${dots}</span>
      <small>${escapeHtml(app.summary)}</small>
    </button>
  `;
}

function renderStage(app, stageId) {
  const stage = app.stages.find((item) => item.id === stageId) ?? {
    id: stageId,
    name: stageId,
    state: "next",
  };
  return `<li data-state="${escapeAttr(stage.state)}">${escapeHtml(stage.name)}</li>`;
}

function renderKeyValue(item) {
  return `<li><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></li>`;
}

function renderEvidence(item) {
  return `<li><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.path)}</strong></li>`;
}

function renderMessage(item) {
  return `<li><span>${escapeHtml(item.sender)}</span><p>${escapeHtml(item.text)}</p></li>`;
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
