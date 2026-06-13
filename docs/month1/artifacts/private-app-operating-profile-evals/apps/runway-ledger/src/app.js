const app = {
  "externalActionsEnabled": false,
  "features": [
    "burn review",
    "invoice follow-up",
    "runway action plan",
    "JSON export"
  ],
  "id": "runway-ledger",
  "intent": "Turn private runway facts into a weekly cash decision board.",
  "marketingIncluded": false,
  "name": "Runway Ledger",
  "privateDomain": "cashflow notes, monthly burn, runway assumptions",
  "signals": [
    {
      "label": "Monthly burn",
      "signal": "reduce optional tooling",
      "value": "4200"
    },
    {
      "label": "Committed revenue",
      "signal": "protect renewal work",
      "value": "1800"
    },
    {
      "label": "Upcoming invoice",
      "signal": "follow up this week",
      "value": "2500"
    }
  ],
  "successMetrics": [
    "cash-risk clarity",
    "weekly action chosen",
    "private data stays local"
  ],
  "user": "solo founder"
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
