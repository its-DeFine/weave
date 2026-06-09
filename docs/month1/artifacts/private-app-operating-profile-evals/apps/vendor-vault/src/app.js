const app = {
  "externalActionsEnabled": false,
  "features": [
    "renewal radar",
    "vendor risk tags",
    "consolidation candidate",
    "JSON export"
  ],
  "id": "vendor-vault",
  "intent": "Compare private vendor notes and decide which renewal needs attention first.",
  "marketingIncluded": false,
  "name": "Vendor Vault",
  "privateDomain": "vendor quotes, renewal dates, service risks",
  "signals": [
    {
      "label": "Hosting vendor",
      "signal": "confirm usage tier",
      "value": "renewal in 30 days"
    },
    {
      "label": "Support vendor",
      "signal": "request SLA evidence",
      "value": "slow response"
    },
    {
      "label": "Analytics vendor",
      "signal": "consider consolidation",
      "value": "duplicate features"
    }
  ],
  "successMetrics": [
    "renewal risk visible",
    "vendor action selected",
    "no external vendor email"
  ],
  "user": "operations manager"
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
