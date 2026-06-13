const app = {
  "externalActionsEnabled": false,
  "features": [
    "queue triage",
    "owner routing",
    "capacity signal",
    "JSON export"
  ],
  "id": "clinic-queue",
  "intent": "Turn clinic operations notes into a queue triage board without health overclaiming.",
  "marketingIncluded": false,
  "name": "Clinic Queue",
  "privateDomain": "appointment backlog, intake bottlenecks, staffing notes",
  "signals": [
    {
      "label": "New intake",
      "signal": "send internal checklist",
      "value": "forms incomplete"
    },
    {
      "label": "Follow-up queue",
      "signal": "reserve nurse slot",
      "value": "capacity tight"
    },
    {
      "label": "Billing question",
      "signal": "route to admin owner",
      "value": "insurance unclear"
    }
  ],
  "successMetrics": [
    "next queue action visible",
    "clinical advice avoided",
    "private notes remain local"
  ],
  "user": "clinic admin"
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
