const storageKey = "launch-studio-textual-v1-state";

const lifecycleItems = [
  {
    id: "positioning",
    label: "Positioning and launch promise reviewed",
    detail: "The founder can state what is launching, for whom, and what is intentionally out of scope."
  },
  {
    id: "offer",
    label: "Offer and pricing boundaries checked",
    detail: "Pricing, free access, paid spend, and promise limits are clear before any public motion."
  },
  {
    id: "ops",
    label: "Operational owner and response path assigned",
    detail: "A responsible owner exists for launch day support, issue triage, and rollback decisions."
  },
  {
    id: "proof",
    label: "Proof artifacts and acceptance checks collected",
    detail: "The review packet has enough evidence to support a launch, caveated launch, or hold."
  }
];

const riskItems = [
  {
    id: "scope-drift",
    severity: "High",
    label: "Scope drift",
    detail: "Launch story claims more than the current product can prove."
  },
  {
    id: "support-load",
    severity: "Medium",
    label: "Support load",
    detail: "Founder has not allocated time for first-response support and issue review."
  },
  {
    id: "qa-gap",
    severity: "High",
    label: "QA gap",
    detail: "Critical flows are not fully walked through on the launch surface."
  },
  {
    id: "seo-thin",
    severity: "Medium",
    label: "SEO thinness",
    detail: "Metadata or page copy does not clearly describe the product and launch intent."
  }
];

const qaItems = [
  {
    id: "happy-path",
    label: "Primary founder review path works",
    detail: "The main readiness flow can be completed without backend dependencies."
  },
  {
    id: "empty-state",
    label: "Empty and reset states are understandable",
    detail: "The cockpit remains useful before any saved review exists."
  },
  {
    id: "responsive",
    label: "Mobile and desktop layouts remain readable",
    detail: "Panels, controls, and notes fit without overlapping."
  },
  {
    id: "local-save",
    label: "Local save and clear behavior verified",
    detail: "Review notes persist only in browser storage and can be cleared."
  }
];

const seoItems = [
  {
    id: "title",
    label: "Page title names the launch cockpit",
    detail: "The browser title and page heading match the product surface."
  },
  {
    id: "description",
    label: "Meta description explains founder value",
    detail: "Search preview text describes launch readiness review clearly."
  },
  {
    id: "og",
    label: "Open Graph title and description present",
    detail: "Shared previews have local static metadata without external media calls."
  },
  {
    id: "semantic",
    label: "Semantic page structure present",
    detail: "The app uses a main landmark and a single top-level h1."
  }
];

const boundaryItems = [
  "Analytics disabled",
  "Deployment disabled",
  "Paid spend disabled",
  "Public sends disabled",
  "Credentials disabled",
  "External API calls disabled"
];

const defaultState = {
  lifecycle: {},
  risks: {},
  qa: {},
  seo: {
    title: true,
    description: true,
    og: true,
    semantic: true
  },
  decision: "Reviewing",
  notes: "",
  savedAt: ""
};

const state = loadState();

function loadState() {
  const saved = localStorage.getItem(storageKey);
  if (!saved) {
    return cloneDefaultState();
  }

  try {
    const parsed = JSON.parse(saved);
    return {
      lifecycle: parsed.lifecycle || {},
      risks: parsed.risks || {},
      qa: parsed.qa || {},
      seo: parsed.seo || defaultState.seo,
      decision: parsed.decision || defaultState.decision,
      notes: parsed.notes || "",
      savedAt: parsed.savedAt || ""
    };
  } catch (error) {
    return cloneDefaultState();
  }
}

function cloneDefaultState() {
  return {
    lifecycle: { ...defaultState.lifecycle },
    risks: { ...defaultState.risks },
    qa: { ...defaultState.qa },
    seo: { ...defaultState.seo },
    decision: defaultState.decision,
    notes: defaultState.notes,
    savedAt: defaultState.savedAt
  };
}

function saveState(markSaved) {
  if (markSaved) {
    state.savedAt = new Date().toLocaleString();
  }

  localStorage.setItem(storageKey, JSON.stringify(state));
  renderSummary();
  renderSavedState();
}

function createCheckItem(group, item) {
  const label = document.createElement("label");
  label.className = "check-row";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = Boolean(state[group][item.id]);
  checkbox.addEventListener("change", () => {
    state[group][item.id] = checkbox.checked;
    saveState(false);
    renderCounts();
  });

  const content = document.createElement("span");
  content.className = "check-copy";

  const title = document.createElement("strong");
  title.textContent = item.label;

  const detail = document.createElement("span");
  detail.textContent = item.detail;

  content.appendChild(title);
  content.appendChild(detail);
  label.appendChild(checkbox);
  label.appendChild(content);

  return label;
}

function createRiskItem(item) {
  const card = document.createElement("article");
  card.className = "risk-card";

  const top = document.createElement("div");
  top.className = "risk-top";

  const title = document.createElement("h3");
  title.textContent = item.label;

  const severity = document.createElement("span");
  severity.className = "severity";
  severity.textContent = item.severity;

  top.appendChild(title);
  top.appendChild(severity);

  const detail = document.createElement("p");
  detail.textContent = item.detail;

  const label = document.createElement("label");
  label.className = "risk-toggle";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = Boolean(state.risks[item.id]);
  checkbox.addEventListener("change", () => {
    state.risks[item.id] = checkbox.checked;
    saveState(false);
    renderCounts();
  });

  const copy = document.createElement("span");
  copy.textContent = "Resolved";

  label.appendChild(checkbox);
  label.appendChild(copy);
  card.appendChild(top);
  card.appendChild(detail);
  card.appendChild(label);

  return card;
}

function createBoundaryItem(text) {
  const item = document.createElement("li");
  const marker = document.createElement("span");
  marker.className = "boundary-marker";
  marker.setAttribute("aria-hidden", "true");

  const copy = document.createElement("span");
  copy.textContent = text;

  item.appendChild(marker);
  item.appendChild(copy);
  return item;
}

function checkedCount(group, items) {
  return items.filter((item) => Boolean(state[group][item.id])).length;
}

function readinessPercent() {
  const total =
    lifecycleItems.length + riskItems.length + qaItems.length + seoItems.length;
  const complete =
    checkedCount("lifecycle", lifecycleItems) +
    checkedCount("risks", riskItems) +
    checkedCount("qa", qaItems) +
    checkedCount("seo", seoItems);

  return Math.round((complete / total) * 100);
}

function renderSummary() {
  const percent = readinessPercent();
  const readinessScore = document.querySelector("#readinessScore");
  const readinessMeter = document.querySelector("#readinessMeter");
  const readinessNarrative = document.querySelector("#readinessNarrative");
  const lifecycleStatus = document.querySelector("#lifecycleStatus");
  const lifecycleNarrative = document.querySelector("#lifecycleNarrative");
  const decisionState = document.querySelector("#decisionState");

  readinessScore.textContent = `${percent}%`;
  readinessMeter.style.width = `${percent}%`;
  decisionState.textContent = state.decision;

  if (percent >= 90) {
    readinessNarrative.textContent = "Most launch checks are complete. Review any caveats before approving public motion.";
  } else if (percent >= 65) {
    readinessNarrative.textContent = "Launch is partially ready. Remaining risks and QA gaps should be owned explicitly.";
  } else {
    readinessNarrative.textContent = "Launch should stay in review until the founder resolves more readiness checks.";
  }

  const lifecycleDone = checkedCount("lifecycle", lifecycleItems);
  if (lifecycleDone === lifecycleItems.length) {
    lifecycleStatus.textContent = "Launch decision ready";
    lifecycleNarrative.textContent = "All lifecycle gates are checked in this local review.";
  } else if (lifecycleDone > 0) {
    lifecycleStatus.textContent = "Pre-launch in progress";
    lifecycleNarrative.textContent = `${lifecycleDone} of ${lifecycleItems.length} lifecycle gates are complete.`;
  } else {
    lifecycleStatus.textContent = "Pre-launch review";
    lifecycleNarrative.textContent = "Start with lifecycle gates before deciding whether to launch.";
  }
}

function renderCounts() {
  const riskOpen = riskItems.length - checkedCount("risks", riskItems);
  const qaDone = checkedCount("qa", qaItems);
  const seoDone = checkedCount("seo", seoItems);

  document.querySelector("#riskCount").textContent = `${riskOpen} open`;
  document.querySelector("#qaCount").textContent = `${qaDone} passed`;
  document.querySelector("#seoCount").textContent = `${seoDone} ready`;
  renderSummary();
}

function renderSavedState() {
  const savedState = document.querySelector("#savedState");
  if (state.savedAt) {
    savedState.textContent = `Saved ${state.savedAt}`;
  } else {
    savedState.textContent = "Not saved";
  }
}

function renderList(targetSelector, group, items) {
  const target = document.querySelector(targetSelector);
  target.replaceChildren();
  items.forEach((item) => {
    target.appendChild(createCheckItem(group, item));
  });
}

function renderRisks() {
  const target = document.querySelector("#riskList");
  target.replaceChildren();
  riskItems.forEach((item) => {
    target.appendChild(createRiskItem(item));
  });
}

function renderBoundaries() {
  const target = document.querySelector("#boundaryList");
  target.replaceChildren();
  boundaryItems.forEach((item) => {
    target.appendChild(createBoundaryItem(item));
  });
}

function renderControls() {
  const decision = document.querySelector("#launchDecision");
  const notes = document.querySelector("#founderNotes");
  const saveButton = document.querySelector("#saveNotes");
  const clearButton = document.querySelector("#clearReview");
  const resetLifecycle = document.querySelector("#resetLifecycle");

  decision.value = state.decision;
  notes.value = state.notes;

  decision.addEventListener("change", () => {
    state.decision = decision.value;
    saveState(false);
  });

  notes.addEventListener("input", () => {
    state.notes = notes.value;
    saveState(false);
  });

  saveButton.addEventListener("click", () => {
    state.decision = decision.value;
    state.notes = notes.value;
    saveState(true);
  });

  clearButton.addEventListener("click", () => {
    localStorage.removeItem(storageKey);
    const fresh = cloneDefaultState();
    state.lifecycle = fresh.lifecycle;
    state.risks = fresh.risks;
    state.qa = fresh.qa;
    state.seo = fresh.seo;
    state.decision = fresh.decision;
    state.notes = fresh.notes;
    state.savedAt = fresh.savedAt;
    renderApp();
  });

  resetLifecycle.addEventListener("click", () => {
    state.lifecycle = {};
    saveState(false);
    renderList("#lifecycleList", "lifecycle", lifecycleItems);
    renderCounts();
  });
}

function renderApp() {
  renderList("#lifecycleList", "lifecycle", lifecycleItems);
  renderRisks();
  renderList("#qaList", "qa", qaItems);
  renderList("#seoList", "seo", seoItems);
  renderBoundaries();
  renderCounts();
  renderSavedState();

  const decision = document.querySelector("#launchDecision");
  const notes = document.querySelector("#founderNotes");
  decision.value = state.decision;
  notes.value = state.notes;
}

document.addEventListener("DOMContentLoaded", () => {
  renderControls();
  renderApp();
});
