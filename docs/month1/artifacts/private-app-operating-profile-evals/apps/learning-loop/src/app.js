const app = {
  "externalActionsEnabled": false,
  "features": [
    "feedback clustering",
    "lesson fix ranking",
    "cohort-safe export",
    "JSON export"
  ],
  "id": "learning-loop",
  "intent": "Find the lesson improvement most likely to help a private cohort.",
  "marketingIncluded": false,
  "name": "Learning Loop",
  "privateDomain": "learner notes, quiz misses, lesson feedback",
  "signals": [
    {
      "label": "Module one",
      "signal": "add glossary",
      "value": "confusing vocabulary"
    },
    {
      "label": "Module two",
      "signal": "shorten assignment",
      "value": "exercise skipped"
    },
    {
      "label": "Module three",
      "signal": "keep structure",
      "value": "high confidence"
    }
  ],
  "successMetrics": [
    "highest leverage lesson named",
    "private feedback summarized",
    "no public claim"
  ],
  "user": "course creator"
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
