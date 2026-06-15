const storageKey = "launch-studio-textual-v1-state";

const defaultState = {
  checks: {},
  riskNote: "",
  decision: "Decision pending"
};

function loadState() {
  const savedState = localStorage.getItem(storageKey);

  if (!savedState) {
    return { ...defaultState };
  }

  try {
    const parsedState = JSON.parse(savedState);
    return {
      checks: parsedState.checks || {},
      riskNote: parsedState.riskNote || "",
      decision: parsedState.decision || defaultState.decision
    };
  } catch {
    return { ...defaultState };
  }
}

function saveState(state) {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function getAreaStatus(area, state) {
  const inputs = Array.from(document.querySelectorAll(`input[data-area="${area}"]`));
  const completed = inputs.filter((input) => state.checks[input.id]).length;

  if (completed === inputs.length) {
    return "Complete";
  }

  if (completed > 0) {
    return `${completed} of ${inputs.length} complete`;
  }

  return "Waiting for checks";
}

function calculateScore(state) {
  const inputs = Array.from(document.querySelectorAll("input[data-weight]"));
  const total = inputs.reduce((sum, input) => sum + Number(input.dataset.weight), 0);
  const earned = inputs.reduce((sum, input) => {
    if (state.checks[input.id]) {
      return sum + Number(input.dataset.weight);
    }

    return sum;
  }, 0);

  if (total === 0) {
    return 0;
  }

  return Math.round((earned / total) * 100);
}

function updateText(id, value) {
  const target = document.getElementById(id);

  if (target) {
    target.textContent = value;
  }
}

function render(state) {
  const score = calculateScore(state);

  updateText("readinessScore", `${score}%`);
  updateText("lifecycleStatus", getAreaStatus("lifecycle", state));
  updateText("qaStatus", getAreaStatus("qa", state));
  updateText("seoStatus", getAreaStatus("seo", state));
  updateText("decisionPill", state.decision);
  updateText("decisionSummary", `Current stance: ${state.decision}`);

  document.querySelectorAll("input[data-weight]").forEach((input) => {
    input.checked = Boolean(state.checks[input.id]);
  });

  const riskNote = document.getElementById("riskNote");
  if (riskNote) {
    riskNote.value = state.riskNote;
  }
}

function assignInputIds() {
  document.querySelectorAll("input[data-weight]").forEach((input, index) => {
    input.id = `readiness-check-${index + 1}`;
  });
}

window.addEventListener("DOMContentLoaded", () => {
  assignInputIds();

  let state = loadState();
  render(state);

  document.querySelectorAll("input[data-weight]").forEach((input) => {
    input.addEventListener("change", () => {
      state = {
        ...state,
        checks: {
          ...state.checks,
          [input.id]: input.checked
        }
      };
      saveState(state);
      render(state);
    });
  });

  const riskNote = document.getElementById("riskNote");
  if (riskNote) {
    riskNote.addEventListener("input", () => {
      state = {
        ...state,
        riskNote: riskNote.value
      };
      saveState(state);
    });
  }

  document.querySelectorAll("button[data-decision]").forEach((button) => {
    button.addEventListener("click", () => {
      state = {
        ...state,
        decision: button.dataset.decision || defaultState.decision
      };
      saveState(state);
      render(state);
    });
  });

  const resetButton = document.getElementById("resetButton");
  if (resetButton) {
    resetButton.addEventListener("click", () => {
      localStorage.removeItem(storageKey);
      state = { ...defaultState };
      render(state);
    });
  }
});
