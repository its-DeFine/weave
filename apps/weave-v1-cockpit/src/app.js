const lifecycle = [
  ["intent", "Intent"],
  ["requirements", "Requirements"],
  ["context_architecture", "Context / Architecture"],
  ["task_breakdown", "Task Breakdown"],
  ["build", "Build"],
  ["review", "Review"],
  ["qa", "QA"],
  ["deploy_readiness", "Deploy Readiness"],
  ["publish", "Publish"],
  ["marketing_iteration_analysis", "Marketing / Iteration / Analysis"]
];

const state = {
  home: "Chief of Staff",
  updateMode: "notify",
  activeAppId: "punch-compute",
  hardGates: [
    "Raw secrets or credential collection",
    "Private topology or private runtime details",
    "Production deploys or service changes",
    "Public sends, posts, or emails",
    "Paid actions or metered jobs"
  ],
  apps: [
    {
      id: "punch-compute",
      name: "Punch Compute",
      summary: "Demand-capture website and launch workflow.",
      stage: "build",
      state: "WORKING",
      next: "Finish local website variants, verify qualified-lead flow, then move to review.",
      proof: [
        ["strategy", "present", "Demand-capture launch strategy exists"],
        ["lead-flow", "pending", "Email verification and qualification proof required"],
        ["release-video", "pending", "Video proof not recorded yet"]
      ],
      blockers: [
        ["lead-integrity", "open", "Need proof that signups are actual people and verified owners of the email address"]
      ],
      workers: [
        ["Codex website worker", "active", "Build static/interactive variants and run local QA"],
        ["Chief of Staff reviewer", "ready_for_review_loop", "Reject sloppy artifacts before DONE"],
        ["Hermes lane", "gated", "Only attach after runtime proof exists"]
      ]
    },
    {
      id: "weave-runtime",
      name: "WEAVE Runtime",
      summary: "Portable Chief-of-Staff layer for Codex and Hermes.",
      stage: "requirements",
      state: "READY_FOR_REVIEW",
      next: "Lock UX paper, service blueprint, state files, update model, and snapshot command.",
      proof: [
        ["ux-paper", "present", "Chief of Staff UX contract drafted"],
        ["service-blueprint", "present", "Backstage state and proof flow drafted"],
        ["cos-cli", "present", "Local state and snapshot command implemented"]
      ],
      blockers: [
        ["live-hermes-claim", "guarded", "Hermes remains adapter-gated until runtime proof exists"]
      ],
      workers: [
        ["Codex implementation", "active", "Create public docs, CLI slice, cockpit, and checks"],
        ["Pro advisor", "consulted", "Critique product/UX/system design"],
        ["Release proof", "pending", "Record screenshots and video"]
      ]
    },
    {
      id: "agentops-hermes",
      name: "AgentOps Hermes",
      summary: "Runtime reinstatement and token-cost audit lane.",
      stage: "review",
      state: "BLOCKED",
      next: "Keep separate from WEAVE public release unless runtime proof is needed.",
      proof: [
        ["audit", "external", "Handled outside this public cockpit slice"]
      ],
      blockers: [
        ["auth", "possible", "Owner auth may be needed for live runtime claims"]
      ],
      workers: [
        ["Hermes maintainer", "separate", "Do not mix private runtime proof into public repo artifacts"]
      ]
    }
  ],
  updates: [
    ["v0.1", "current", "Chief-of-Staff home, lifecycle rail, proof tray, blocker tray, update inbox"],
    ["v0.2 idea", "notify", "Worker blocker sharing and advisor review ledger"],
    ["daily check", "planned", "Read public version metadata and surface useful changes in the Chief of Staff home"]
  ]
};

const viewTitles = {
  overview: "Overview",
  lifecycle: "Lifecycle",
  workers: "Workers",
  proof: "Proof",
  updates: "Updates"
};

const query = new URLSearchParams(window.location.search);
const initialView = query.get("view");
const initialApp = query.get("app");

let activeTab = Object.prototype.hasOwnProperty.call(viewTitles, initialView) ? initialView : "overview";

if (initialApp && state.apps.some((app) => app.id === initialApp)) {
  state.activeAppId = initialApp;
}

function activeApp() {
  return state.apps.find((app) => app.id === state.activeAppId) || state.apps[0];
}

function stageLabel(stageId) {
  const row = lifecycle.find(([id]) => id === stageId);
  return row ? row[1] : stageId.replaceAll("_", " ");
}

function stateLine() {
  const app = activeApp();
  return `WEAVE | Home=${state.home} | App=${app.name} | Stage=${stageLabel(app.stage)} | State=${app.state} | Next=${compactNext(app)} | Mode=${state.updateMode}`;
}

function compactNext(app) {
  if (app.id === "punch-compute") return "verify lead flow, then review";
  if (app.id === "weave-runtime") return "lock blueprint and snapshot proof";
  return "keep private runtime proof separate";
}

function stateLineParts(app) {
  return [
    "WEAVE",
    `Home=${state.home}`,
    `App=${app.name}`,
    `Stage=${stageLabel(app.stage)}`,
    `State=${app.state}`,
    `Next=${compactNext(app)}`,
    `Mode=${state.updateMode}`
  ];
}

function stageState(app, stageId) {
  const activeIndex = lifecycle.findIndex(([id]) => id === app.stage);
  const index = lifecycle.findIndex(([id]) => id === stageId);
  if (index < activeIndex) return "complete";
  if (index === activeIndex) return "active";
  return "locked";
}

function renderAppList() {
  const root = document.querySelector("#appList");
  root.innerHTML = "";
  state.apps.forEach((app) => {
    const button = document.createElement("button");
    button.className = `app-card ${app.id === state.activeAppId ? "is-active" : ""}`;
    button.type = "button";
    button.dataset.appId = app.id;
    button.innerHTML = `
      <strong>${app.name}</strong>
      <span>${stageLabel(app.stage)}</span>
      <em>${app.state}</em>
    `;
    button.addEventListener("click", () => {
      state.activeAppId = app.id;
      render();
    });
    root.appendChild(button);
  });
  document.querySelector("#appCount").textContent = `${state.apps.length} active`;
}

function renderOverview(app) {
  return `
    <div class="overview-grid">
      <section class="metric-block">
        <span>App</span>
        <strong>${app.name}</strong>
        <p>${app.summary}</p>
      </section>
      <section class="metric-block">
        <span>Current Stage</span>
        <strong>${stageLabel(app.stage)}</strong>
        <p>${app.state}</p>
      </section>
      <section class="metric-block">
        <span>Proof State</span>
        <strong>${app.proof.filter((item) => item[1] === "present").length}/${app.proof.length} present</strong>
        <p>DONE is blocked until required proof is present.</p>
      </section>
      <section class="metric-block">
        <span>Worker Lanes</span>
        <strong>${app.workers.length}</strong>
        <p>Workers must return proof to this home.</p>
      </section>
    </div>
    <div class="state-strip">
      <span>READY_FOR_REVIEW is not DONE</span>
      <span>Missing gates are named</span>
      <span>Live effects require exact approval</span>
    </div>
  `;
}

function renderLifecycle(app) {
  const items = lifecycle.map(([id, label]) => {
    const status = stageState(app, id);
    return `
      <li class="stage-row stage-${status}">
        <span>${label}</span>
        <strong>${status}</strong>
      </li>
    `;
  }).join("");
  return `<ol class="stage-list">${items}</ol>`;
}

function renderWorkers(app) {
  const rows = app.workers.map(([label, status, detail]) => `
    <li class="detail-row">
      <strong>${label}</strong>
      <span>${status}</span>
      <em>${detail}</em>
    </li>
  `).join("");
  return `
    <ul class="detail-list">${rows}</ul>
    <div class="packet-preview" id="packetBox">
      <strong>Worker packet preview</strong>
      <pre>{
  "app": "${app.id}",
  "stage": "${app.stage}",
  "allowed_surfaces": ["repo", "local_tests", "public_docs"],
  "forbidden_surfaces": ["raw_secrets", "production_deploy", "public_send"],
  "proof_path": "weave-home/apps/${app.id}/proof/"
}</pre>
    </div>
  `;
}

function renderProof(app) {
  const proofRows = app.proof.map(([label, status, detail]) => `
    <li class="detail-row proof-${status}">
      <strong>${label}</strong>
      <span>${status}</span>
      <em>${detail}</em>
    </li>
  `).join("");
  const blockerRows = app.blockers.map(([label, status, detail]) => `
    <li class="detail-row blocker">
      <strong>${label}</strong>
      <span>${status}</span>
      <em>${detail}</em>
    </li>
  `).join("");
  return `
    <div class="two-column">
      <section>
        <h3>Proof Tray</h3>
        <ul class="detail-list">${proofRows}</ul>
      </section>
      <section>
        <h3>Blocker Tray</h3>
        <ul class="detail-list">${blockerRows}</ul>
      </section>
    </div>
  `;
}

function renderUpdates() {
  const rows = state.updates.map(([label, status, detail]) => `
    <li class="detail-row">
      <strong>${label}</strong>
      <span>${status}</span>
      <em>${detail}</em>
    </li>
  `).join("");
  return `
    <ul class="detail-list">${rows}</ul>
    <p class="note">Behavior-changing updates are review items. Safe docs/schema clarifications can be auto-applied only in auto-safe mode.</p>
  `;
}

function renderMainView(app) {
  const root = document.querySelector("#viewRoot");
  const renderers = {
    overview: () => renderOverview(app),
    lifecycle: () => renderLifecycle(app),
    workers: () => renderWorkers(app),
    proof: () => renderProof(app),
    updates: () => renderUpdates(app)
  };
  root.innerHTML = renderers[activeTab]();
}

function renderSide(app) {
  document.querySelector("#currentStagePill").textContent = stageLabel(app.stage);
  document.querySelector("#nextAction").textContent = app.next;
  const gates = document.querySelector("#gateList");
  gates.innerHTML = state.hardGates.map((gate) => `<li>${gate}</li>`).join("");
}

function renderTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === activeTab);
  });
}

function render() {
  const app = activeApp();
  const stateLineRoot = document.querySelector("#stateLine");
  stateLineRoot.replaceChildren(...stateLineParts(app).map((part) => {
    const item = document.createElement("span");
    item.textContent = part;
    return item;
  }));
  document.querySelector("#viewTitle").textContent = viewTitles[activeTab];
  document.querySelector("#viewSubtitle").textContent = app.name;
  renderTabs();
  renderAppList();
  renderMainView(app);
  renderSide(app);
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    activeTab = button.dataset.tab;
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.set("view", activeTab);
    nextUrl.searchParams.set("app", state.activeAppId);
    window.history.replaceState({}, "", nextUrl);
    render();
  });
});

document.querySelector("#advancePreview").addEventListener("click", () => {
  const app = activeApp();
  const currentIndex = lifecycle.findIndex(([id]) => id === app.stage);
  const nextRow = lifecycle[Math.min(currentIndex + 1, lifecycle.length - 1)];
  app.stage = nextRow[0];
  app.state = nextRow[0] === "publish" ? "blocked_before_public_action" : "ready_for_review";
  app.next = nextRow[0] === "publish"
    ? "stop before public publication until exact owner approval"
    : `review proof for ${nextRow[1]} before marking DONE`;
  activeTab = "lifecycle";
  render();
});

document.querySelector("#packetPreview").addEventListener("click", () => {
  activeTab = "workers";
  render();
  const packet = document.querySelector("#packetBox");
  if (packet) packet.scrollIntoView({ block: "nearest", behavior: "smooth" });
});

render();
