const STORAGE_KEY = "launch-studio-textual-v1-state";

const reviewGroups = {
  lifecycle: [
    {
      id: "positioning",
      title: "Positioning and offer",
      detail: "Audience, promise, pricing, and launch claim are reviewable."
    },
    {
      id: "onboarding",
      title: "First-run path",
      detail: "A new visitor can reach the core value without founder intervention."
    },
    {
      id: "operations",
      title: "Support and rollback",
      detail: "Support owner, escalation path, and rollback condition are named."
    },
    {
      id: "measurement",
      title: "Manual measurement",
      detail: "Launch outcomes can be reviewed without analytics beacons."
    }
  ],
  risk: [
    {
      id: "scope-creep",
      title: "Scope creep",
      detail: "Launch promise exceeds the product state or support capacity."
    },
    {
      id: "broken-core-path",
      title: "Broken core path",
      detail: "Primary path is untested on a fresh browser session."
    },
    {
      id: "unclear-boundary",
      title: "Unclear boundary",
      detail: "Users could infer deployment, spending, or public-send behavior."
    }
  ],
  qa: [
    {
      id: "responsive-layout",
      title: "Responsive layout",
      detail: "Cockpit remains legible on narrow and wide screens."
    },
    {
      id: "state-persistence",
      title: "State persistence",
      detail: "Founder notes and review states persist locally."
    },
    {
      id: "keyboard-flow",
      title: "Keyboard flow",
      detail: "Buttons, text fields, and sections remain reachable."
    }
  ],
  seo: [
    {
      id: "title-meta",
      title: "Title and description",
      detail: "Page title, meta description, and Open Graph copy are present."
    },
    {
      id: "semantic-structure",
      title: "Semantic structure",
      detail: "Main landmark, headings, labels, and readable copy are in place."
    },
    {
      id: "share-copy",
      title: "Share copy",
      detail: "External-facing launch summary is concise and bounded."
    }
  ]
};

const boundaries = [
  "Local-only static cockpit",
  "Analytics disabled",
  "Deployment disabled",
  "Paid spend disabled",
  "Public sends disabled",
  "Credentials disabled",
  "No external API calls"
];

const statusOrder = ["block", "watch", "ready"];

const statusLabels = {
  block: "Blocked",
  watch: "Watch",
  ready: "Ready"
};

const defaultState = {
  decision: "hold",
  notes: "",
  updatedAt: "",
  items: {
    positioning: "watch",
    onboarding: "watch",
    operations: "block",
    measurement: "watch",
    "scope-creep": "watch",
    "broken-core-path": "block",
    "unclear-boundary": "watch",
    "responsive-layout": "watch",
    "state-persistence": "ready",
    "keyboard-flow": "watch",
    "title-meta": "ready",
    "semantic-structure": "ready",
    "share-copy": "watch"
  }
};

const appState = loadState();

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);

  if (!saved) {
    return structuredClone(defaultState);
  }

  try {
    const parsed = JSON.parse(saved);
    return {
      ...structuredClone(defaultState),
      ...parsed,
      items: {
        ...defaultState.items,
        ...(parsed.items || {})
      }
    };
  } catch (error) {
    return structuredClone(defaultState);
  }
}

function saveState(message) {
  appState.updatedAt = new Date().toISOString();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(appState));
  setText("save-state", message);
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = value;
  }
}

function createNode(tagName, className, text) {
  const node = document.createElement(tagName);

  if (className) {
    node.className = className;
  }

  if (text !== undefined) {
    node.textContent = text;
  }

  return node;
}

function nextStatus(current) {
  const currentIndex = statusOrder.indexOf(current);
  return statusOrder[(currentIndex + 1) % statusOrder.length];
}

function renderReviewGroup(groupName, targetId) {
  const target = document.getElementById(targetId);
  target.textContent = "";

  reviewGroups[groupName].forEach((item) => {
    const status = appState.items[item.id] || "watch";
    const row = createNode("div", `review-item ${status}`);
    const copy = createNode("div", "review-copy");
    const title = createNode("h3", "", item.title);
    const detail = createNode("p", "", item.detail);
    const button = createNode("button", `status-button ${status}`, statusLabels[status]);

    button.type = "button";
    button.setAttribute("aria-label", `${item.title}: ${statusLabels[status]}`);
    button.addEventListener("click", () => {
      appState.items[item.id] = nextStatus(status);
      saveState("Review saved locally");
      renderApp();
    });

    copy.append(title, detail);
    row.append(copy, button);
    target.appendChild(row);
  });
}

function countGroup(groupName, wantedStatus) {
  return reviewGroups[groupName].filter((item) => appState.items[item.id] === wantedStatus).length;
}

function allItems() {
  return Object.values(reviewGroups).flat();
}

function readiness() {
  const items = allItems();
  const readyCount = items.filter((item) => appState.items[item.id] === "ready").length;
  const blockedCount = items.filter((item) => appState.items[item.id] === "block").length;
  const baseScore = Math.round((readyCount / items.length) * 100);
  const adjustedScore = Math.max(0, baseScore - blockedCount * 8);

  return {
    score: adjustedScore,
    readyCount,
    blockedCount,
    total: items.length
  };
}

function renderCounts() {
  const current = readiness();
  let label = "Needs review";

  if (current.blockedCount > 0) {
    label = "Blocked";
  } else if (current.score >= 85 && appState.decision === "go") {
    label = "Launchable";
  } else if (current.score >= 70) {
    label = "Limited launch";
  }

  setText("readiness-score", `${current.score}%`);
  setText("readiness-label", label);
  setText("lifecycle-count", `${countGroup("lifecycle", "ready")} ready`);
  setText("risk-count", `${reviewGroups.risk.length - countGroup("risk", "ready")} open`);
  setText("qa-count", `${countGroup("qa", "ready")} pass`);
  setText("seo-count", `${countGroup("seo", "ready")} complete`);
}

function renderBoundaries() {
  const target = document.getElementById("boundary-list");
  target.textContent = "";

  boundaries.forEach((boundary) => {
    const item = createNode("li", "", boundary);
    target.appendChild(item);
  });
}

function renderDecisionButtons() {
  document.querySelectorAll("[data-decision]").forEach((button) => {
    const isActive = button.dataset.decision === appState.decision;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function renderNotes() {
  const notes = document.getElementById("decision-notes");

  if (notes.value !== appState.notes) {
    notes.value = appState.notes;
  }

  if (appState.updatedAt) {
    setText("save-state", `Saved locally at ${new Date(appState.updatedAt).toLocaleString()}`);
  }
}

function renderApp() {
  renderReviewGroup("lifecycle", "lifecycle-list");
  renderReviewGroup("risk", "risk-list");
  renderReviewGroup("qa", "qa-list");
  renderReviewGroup("seo", "seo-list");
  renderBoundaries();
  renderDecisionButtons();
  renderCounts();
  renderNotes();
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-decision]").forEach((button) => {
    button.addEventListener("click", () => {
      appState.decision = button.dataset.decision;
      saveState("Decision saved locally");
      renderApp();
    });
  });

  document.getElementById("decision-notes").addEventListener("input", (event) => {
    appState.notes = event.target.value;
    saveState("Notes saved locally");
  });

  document.getElementById("save-button").addEventListener("click", () => {
    saveState("Review saved locally");
    renderApp();
  });

  document.getElementById("reset-button").addEventListener("click", () => {
    const freshState = structuredClone(defaultState);
    Object.assign(appState, freshState);
    saveState("Review reset locally");
    renderApp();
  });

  renderApp();
});
