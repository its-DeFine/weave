const app = {
  "externalActionsEnabled": false,
  "features": [
    "daily checklist",
    "gentle priority",
    "handoff note",
    "JSON export"
  ],
  "id": "care-loop",
  "intent": "Turn private care reminders into a calm daily checklist.",
  "marketingIncluded": false,
  "name": "Care Loop",
  "privateDomain": "care tasks, check-ins, household routines",
  "signals": [
    {
      "label": "Morning medication",
      "signal": "confirm before breakfast",
      "value": "daily"
    },
    {
      "label": "Hydration check",
      "signal": "make visible",
      "value": "afternoon"
    },
    {
      "label": "Evening note",
      "signal": "capture pattern",
      "value": "mood and sleep"
    }
  ],
  "successMetrics": [
    "less missed routine",
    "reviewable handoff",
    "no health overclaim"
  ],
  "user": "care coordinator"
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
