const app = {
  "externalActionsEnabled": false,
  "features": [
    "cohort signal cards",
    "friction ranking",
    "fix-first decision",
    "JSON export"
  ],
  "id": "cohort-compass",
  "intent": "Help a product operator decide which activation friction to fix first.",
  "marketingIncluded": false,
  "name": "Cohort Compass",
  "privateDomain": "usage cohorts, activation notes, churn reasons",
  "signals": [
    {
      "label": "New users",
      "signal": "improve first-session guidance",
      "value": "low activation"
    },
    {
      "label": "Returning users",
      "signal": "protect export workflow",
      "value": "high export usage"
    },
    {
      "label": "Churn notes",
      "signal": "add onboarding checklist",
      "value": "unclear setup"
    }
  ],
  "successMetrics": [
    "top friction named",
    "fix candidate selected",
    "evidence trace exists"
  ],
  "user": "product operator"
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
