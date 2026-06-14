const app = {
  "externalActionsEnabled": false,
  "features": [
    "grant priority board",
    "missing-material checklist",
    "deadline risk",
    "JSON export"
  ],
  "id": "grant-radar",
  "intent": "Prioritize private grant opportunities and missing application materials.",
  "marketingIncluded": false,
  "name": "Grant Radar",
  "privateDomain": "grant deadlines, eligibility notes, draft application gaps",
  "signals": [
    {
      "label": "City grant",
      "signal": "finish budget appendix",
      "value": "deadline in 18 days"
    },
    {
      "label": "Foundation grant",
      "signal": "request letter this week",
      "value": "requires partner letter"
    },
    {
      "label": "Pilot fund",
      "signal": "clarify nonprofit status requirement",
      "value": "eligibility unclear"
    }
  ],
  "successMetrics": [
    "highest-priority grant named",
    "missing material explicit",
    "no funder contact sent"
  ],
  "user": "nonprofit operator"
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
