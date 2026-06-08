const DEFAULT_INPUT = {
  title: "Lanterns Over Oryn",
  audience: "solo founders",
  premise: "a small team turns rough product intent into a playable story pitch",
  tone: "hopeful",
  style: "storybook",
  sceneCount: 4,
  priceCents: 900,
};

const TONE_BANK = {
  hopeful: {
    palette: ["#f8d66d", "#9bcf9f", "#5a7d9a", "#f7f1df"],
    verbs: ["opens", "steadies", "guides", "returns"],
    stakes: "clarity before momentum",
  },
  tense: {
    palette: ["#e46f5a", "#27374d", "#8fb0a9", "#f5ead7"],
    verbs: ["fractures", "questions", "presses", "reveals"],
    stakes: "trust before scale",
  },
  curious: {
    palette: ["#7aa6c2", "#f2b880", "#7a9a68", "#fbf7ef"],
    verbs: ["notices", "tests", "maps", "connects"],
    stakes: "evidence before certainty",
  },
};

const STYLE_BANK = {
  storybook: {
    hero: "field guide",
    visualCue: "soft hills, warm lamps, handwritten notes",
  },
  noir: {
    hero: "case board",
    visualCue: "deep contrast, side light, narrow streets",
  },
  arcade: {
    hero: "quest screen",
    visualCue: "bold panels, score counters, saturated props",
  },
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, Number(value) || min));
}

function clean(value, fallback) {
  const text = String(value || "").trim();
  return text || fallback;
}

function hashText(value) {
  let hash = 2166136261;
  for (const char of String(value)) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return Math.abs(hash >>> 0);
}

function choice(seed, values) {
  return values[seed % values.length];
}

export function normalizeInput(input = {}) {
  return {
    title: clean(input.title, DEFAULT_INPUT.title).slice(0, 64),
    audience: clean(input.audience, DEFAULT_INPUT.audience).slice(0, 80),
    premise: clean(input.premise, DEFAULT_INPUT.premise).slice(0, 220),
    tone: TONE_BANK[input.tone] ? input.tone : DEFAULT_INPUT.tone,
    style: STYLE_BANK[input.style] ? input.style : DEFAULT_INPUT.style,
    sceneCount: clamp(input.sceneCount, 3, 6),
    priceCents: clamp(input.priceCents || DEFAULT_INPUT.priceCents, 100, 9900),
  };
}

export function createStory(input = {}) {
  const normalized = normalizeInput(input);
  const tone = TONE_BANK[normalized.tone];
  const style = STYLE_BANK[normalized.style];
  const storyHash = hashText(`${normalized.title}|${normalized.audience}|${normalized.premise}`);
  const scenes = Array.from({ length: normalized.sceneCount }, (_, index) => {
    const sceneHash = storyHash + index * 17;
    const verb = choice(sceneHash, tone.verbs);
    const beat = [
      `A ${style.hero} ${verb} around ${normalized.premise}.`,
      `The audience sees ${tone.stakes} turn into a visible choice.`,
      `A concrete artifact appears before the next decision is allowed.`,
      `The last panel asks whether the proof is strong enough to share.`,
      `The loop returns with feedback instead of pretending the first pass is final.`,
      `The monetization test stays visible but inactive until configured.`,
    ][index];
    return {
      id: `scene-${index + 1}`,
      title: `Scene ${index + 1}`,
      beat,
      narration: `${beat} Built for ${normalized.audience}.`,
      choices: [
        `Collect one more proof point for ${normalized.audience}`,
        `Make the next artifact smaller and clearer`,
      ],
      visual: {
        palette: tone.palette,
        prop: choice(sceneHash, ["lantern", "map", "ticket", "mirror", "signal", "notebook"]),
        height: 38 + index * 8,
        offset: (sceneHash % 7) + 2,
      },
    };
  });
  const kpis = calculateKpis({ input: normalized, scenes });
  return {
    schema: "fableframe-story/v0.1",
    createdAt: new Date().toISOString(),
    input: normalized,
    title: normalized.title,
    pitch: `${normalized.title} is a ${normalized.tone} ${normalized.style} visual-novel pitch for ${normalized.audience}.`,
    scenes,
    kpis,
    monetization: monetizationState({ priceCents: normalized.priceCents }),
  };
}

export function calculateKpis(story) {
  const input = story.input || normalizeInput();
  const sceneCount = story.scenes?.length || input.sceneCount;
  const premiseWeight = Math.min(40, Math.round(input.premise.length / 4));
  const audienceWeight = Math.min(25, Math.round(input.audience.length / 3));
  const completionEstimate = Math.min(92, 48 + sceneCount * 6 + premiseWeight);
  const shareIntent = Math.min(88, 35 + audienceWeight + sceneCount * 5);
  const conversionIntent = Math.min(24, 5 + Math.round((completionEstimate + shareIntent) / 18));
  return {
    completionEstimate,
    shareIntent,
    conversionIntent,
    feedbackTarget: Math.max(8, sceneCount * 4),
  };
}

export function applyFeedback(story, feedback = {}) {
  const text = clean(feedback.note, "make the value clearer before asking for payment");
  const revised = structuredClone(story);
  revised.iteration = {
    receivedAt: new Date().toISOString(),
    note: text,
    action: "tightened first-scene value proposition and moved payment ask after proof",
  };
  revised.scenes = revised.scenes.map((scene, index) => {
    if (index !== 0) {
      return scene;
    }
    return {
      ...scene,
      narration: `${scene.narration} Iteration note: ${text}.`,
      choices: ["Show proof first", ...scene.choices.slice(0, 1)],
    };
  });
  revised.kpis = {
    ...calculateKpis(revised),
    conversionIntent: Math.min(35, calculateKpis(revised).conversionIntent + 4),
  };
  return revised;
}

export function monetizationState(config = {}) {
  const checkoutUrl = clean(config.checkoutUrl, "");
  const priceCents = clamp(config.priceCents || DEFAULT_INPUT.priceCents, 100, 9900);
  const enabled = /^https:\/\/.+/i.test(checkoutUrl);
  return {
    enabled,
    checkoutUrl: enabled ? checkoutUrl : "",
    priceCents,
    priceLabel: `$${(priceCents / 100).toFixed(2)}`,
    status: enabled ? "checkout_configured" : "checkout_not_configured",
  };
}

export function exportStory(story) {
  return {
    schema: "fableframe-export/v0.1",
    exportedAt: new Date().toISOString(),
    title: story.title,
    pitch: story.pitch,
    scenes: story.scenes,
    kpis: story.kpis,
    monetization: story.monetization,
    iteration: story.iteration || null,
  };
}

export { DEFAULT_INPUT, STYLE_BANK, TONE_BANK };
