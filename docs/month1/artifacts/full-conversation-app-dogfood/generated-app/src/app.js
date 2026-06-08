const planList = document.querySelector('#plan-list');
const exportOutput = document.querySelector('#export-output');
const seedInputs = ['#seed-one', '#seed-two', '#seed-three'].map((selector) => document.querySelector(selector));

function seedValue(input, index) {
  const value = input.value.trim();
  return value || `Untitled seed ${index + 1}`;
}

function buildPlan() {
  return seedInputs.map(seedValue).map((seed, index) => ({
    priority: index + 1,
    seed,
    nextAction: index === 0 ? `Validate: ${seed}` : index === 1 ? `Prototype: ${seed}` : `Defer safely: ${seed}`,
    effort: index === 0 ? '45 minutes' : index === 1 ? '90 minutes' : 'owner-approved future work',
    externalAction: false
  }));
}

function renderPlan() {
  const plan = buildPlan();
  planList.innerHTML = '';
  plan.forEach((item) => {
    const row = document.createElement('li');
    row.innerHTML = `<strong>${item.nextAction}</strong><br><span>Effort: ${item.effort}</span>`;
    planList.appendChild(row);
  });
  return plan;
}

function exportPlan() {
  const payload = {
    schema: 'pocket-orchard-plan/v0.1',
    generatedBy: 'weave-full-conversation-dogfood',
    localOnly: true,
    externalActionsEnabled: false,
    plan: renderPlan()
  };
  exportOutput.textContent = JSON.stringify(payload, null, 2);
  return payload;
}

document.querySelector('#grow-plan').addEventListener('click', renderPlan);
document.querySelector('#export-plan').addEventListener('click', exportPlan);
renderPlan();
window.PocketOrchard = { buildPlan, exportPlan };
