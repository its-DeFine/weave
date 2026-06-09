const app = {
  "externalActionsEnabled": false,
  "features": [
    "objection board",
    "follow-up planner",
    "risk tag summary",
    "JSON export"
  ],
  "id": "partner-pulse",
  "intent": "Convert partner notes into follow-up priorities and risk tags.",
  "marketingIncluded": false,
  "name": "Partner Pulse",
  "privateDomain": "partner conversations, objections, follow-up commitments",
  "signals": [
    {
      "label": "Analytics partner",
      "signal": "needs technical owner",
      "value": "integration blocker"
    },
    {
      "label": "Agency channel",
      "signal": "clarify package tiers",
      "value": "pricing confusion"
    },
    {
      "label": "Infra partner",
      "signal": "send local demo evidence",
      "value": "waiting on proof"
    }
  ],
  "successMetrics": [
    "next partner action",
    "objection pattern visible",
    "no public send"
  ],
  "user": "partnership lead"
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function renderSignals() {
  document.getElementById('intent').textContent = app.intent;
  const container = document.getElementById('signals');
  app.signals.forEach((signal, index) => {
    const card = el('article', 'card');
    card.appendChild(el('h3', '', `${index + 1}. ${signal.label}`));
    card.appendChild(el('p', 'value', signal.value));
    card.appendChild(el('p', 'signal', signal.signal));
    container.appendChild(card);
  });
}

function buildActions() {
  return app.signals.map((signal, index) => ({
    rank: index + 1,
    action: signal.signal,
    evidence: signal.label,
    privateDataUsed: true,
    publicSendAllowed: false
  }));
}

function renderActions() {
  const actions = document.getElementById('actions');
  buildActions().forEach(item => {
    const row = el('li', 'action');
    row.appendChild(el('strong', '', item.action));
    row.appendChild(el('span', '', ` Evidence: ${item.evidence}`));
    actions.appendChild(row);
  });
}

function exportAssessment() {
  const exportPayload = {
    schema: 'weave-private-app-export/v0.1',
    appId: app.id,
    appName: app.name,
    generatedFromPrivateData: true,
    externalActionsEnabled: app.externalActionsEnabled,
    marketingIncluded: app.marketingIncluded,
    successMetrics: app.successMetrics,
    recommendedActions: buildActions()
  };
  document.getElementById('exportPreview').textContent = JSON.stringify(exportPayload, null, 2);
}

renderSignals();
renderActions();
document.getElementById('exportButton').addEventListener('click', exportAssessment);
