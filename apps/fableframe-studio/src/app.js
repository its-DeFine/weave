import {
  DEFAULT_INPUT,
  applyFeedback,
  createStory,
  exportStory,
  monetizationState,
} from "./story-engine.mjs";

const state = {
  story: createStory(DEFAULT_INPUT),
  selectedScene: 0,
  config: { checkoutUrl: "", priceCents: DEFAULT_INPUT.priceCents },
};

const refs = {};

function byId(id) {
  return document.getElementById(id);
}

function bindRefs() {
  [
    "title",
    "audience",
    "premise",
    "tone",
    "style",
    "sceneCount",
    "priceCents",
    "generate",
    "iterate",
    "exportJson",
    "copyPitch",
    "checkout",
    "sceneTabs",
    "sceneTitle",
    "sceneNarration",
    "choiceList",
    "pitch",
    "kpiCompletion",
    "kpiShare",
    "kpiConversion",
    "monetizationStatus",
    "priceLabel",
    "checkoutState",
    "feedbackNote",
    "artifactState",
    "stageState",
    "canvas",
  ].forEach((id) => {
    refs[id] = byId(id);
  });
}

async function loadConfig() {
  try {
    const response = await fetch("./public/config.json", { cache: "no-store" });
    if (response.ok) {
      const config = await response.json();
      state.config = {
        checkoutUrl: config.checkoutUrl || "",
        priceCents: Number(config.priceCents || DEFAULT_INPUT.priceCents),
      };
    }
  } catch {
    state.config = { checkoutUrl: "", priceCents: DEFAULT_INPUT.priceCents };
  }
}

function formInput() {
  return {
    title: refs.title.value,
    audience: refs.audience.value,
    premise: refs.premise.value,
    tone: refs.tone.value,
    style: refs.style.value,
    sceneCount: Number(refs.sceneCount.value),
    priceCents: Number(refs.priceCents.value),
  };
}

function setDefaults() {
  refs.title.value = DEFAULT_INPUT.title;
  refs.audience.value = DEFAULT_INPUT.audience;
  refs.premise.value = DEFAULT_INPUT.premise;
  refs.tone.value = DEFAULT_INPUT.tone;
  refs.style.value = DEFAULT_INPUT.style;
  refs.sceneCount.value = String(DEFAULT_INPUT.sceneCount);
  refs.priceCents.value = String(DEFAULT_INPUT.priceCents);
}

function renderTabs() {
  refs.sceneTabs.innerHTML = "";
  state.story.scenes.forEach((scene, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = index === state.selectedScene ? "tab is-active" : "tab";
    button.textContent = scene.title;
    button.addEventListener("click", () => {
      state.selectedScene = index;
      render();
    });
    refs.sceneTabs.append(button);
  });
}

function renderScene() {
  const scene = state.story.scenes[state.selectedScene];
  refs.sceneTitle.textContent = scene.title;
  refs.sceneNarration.textContent = scene.narration;
  refs.choiceList.innerHTML = "";
  scene.choices.forEach((choice) => {
    const item = document.createElement("li");
    item.textContent = choice;
    refs.choiceList.append(item);
  });
  drawScene(scene);
}

function drawScene(scene) {
  const canvas = refs.canvas;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(320, Math.round(rect.width * window.devicePixelRatio));
  const height = Math.max(220, Math.round(rect.height * window.devicePixelRatio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const ctx = canvas.getContext("2d");
  const [sun, hill, ink, paper] = scene.visual.palette;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = sun;
  ctx.beginPath();
  ctx.arc(width * 0.78, height * 0.22, height * 0.09, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = hill;
  ctx.beginPath();
  ctx.moveTo(0, height * 0.68);
  ctx.quadraticCurveTo(width * 0.32, height * 0.36, width * 0.64, height * 0.62);
  ctx.quadraticCurveTo(width * 0.84, height * 0.8, width, height * 0.56);
  ctx.lineTo(width, height);
  ctx.lineTo(0, height);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = ink;
  ctx.lineWidth = Math.max(4, width * 0.006);
  ctx.strokeRect(width * 0.08, height * 0.14, width * 0.84, height * 0.72);
  ctx.fillStyle = ink;
  const x = width * (0.28 + scene.visual.offset / 24);
  const y = height * 0.56;
  ctx.beginPath();
  ctx.arc(x, y, height * 0.06, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillRect(x - width * 0.025, y + height * 0.055, width * 0.05, height * 0.16);
  ctx.fillStyle = sun;
  ctx.fillRect(width * 0.12, height * 0.76, width * 0.32, height * 0.05);
  ctx.fillStyle = ink;
  ctx.font = `${Math.max(14, Math.round(height * 0.055))}px system-ui, sans-serif`;
  ctx.fillText(scene.visual.prop, width * 0.14, height * 0.8);
}

function renderMetrics() {
  refs.pitch.textContent = state.story.pitch;
  refs.kpiCompletion.textContent = `${state.story.kpis.completionEstimate}%`;
  refs.kpiShare.textContent = `${state.story.kpis.shareIntent}%`;
  refs.kpiConversion.textContent = `${state.story.kpis.conversionIntent}%`;
  const config = {
    checkoutUrl: state.config.checkoutUrl,
    priceCents: Number(refs.priceCents.value || state.config.priceCents),
  };
  state.story.monetization = monetizationState(config);
  refs.monetizationStatus.textContent = state.story.monetization.enabled ? "Configured" : "Draft";
  refs.priceLabel.textContent = state.story.monetization.priceLabel;
  refs.checkoutState.textContent = state.story.monetization.status;
  refs.checkout.disabled = !state.story.monetization.enabled;
  refs.artifactState.textContent = `${state.story.scenes.length} scenes`;
  refs.stageState.textContent = state.story.iteration ? "iteration" : "qa-ready";
}

function render() {
  renderTabs();
  renderScene();
  renderMetrics();
}

function generate() {
  state.story = createStory(formInput());
  state.selectedScene = 0;
  refs.feedbackNote.value = "";
  render();
}

function iterate() {
  const note = refs.feedbackNote.value || "the first scene needs a clearer reason to pay";
  state.story = applyFeedback(state.story, { note });
  state.selectedScene = 0;
  render();
}

function downloadJson() {
  const payload = JSON.stringify(exportStory(state.story), null, 2);
  const blob = new Blob([payload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${state.story.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function copyPitch() {
  await navigator.clipboard.writeText(state.story.pitch);
  refs.copyPitch.textContent = "Copied";
  window.setTimeout(() => {
    refs.copyPitch.textContent = "Copy pitch";
  }, 1200);
}

function goCheckout() {
  if (!state.story.monetization.enabled) {
    return;
  }
  window.location.href = state.story.monetization.checkoutUrl;
}

function bindEvents() {
  refs.generate.addEventListener("click", generate);
  refs.iterate.addEventListener("click", iterate);
  refs.exportJson.addEventListener("click", downloadJson);
  refs.copyPitch.addEventListener("click", copyPitch);
  refs.checkout.addEventListener("click", goCheckout);
  refs.sceneCount.addEventListener("input", () => {
    byId("sceneCountValue").textContent = refs.sceneCount.value;
  });
  window.addEventListener("resize", () => renderScene());
}

async function main() {
  bindRefs();
  setDefaults();
  bindEvents();
  await loadConfig();
  render();
}

main();
