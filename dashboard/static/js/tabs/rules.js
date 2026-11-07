// Rules: game rules with presets. Applied live and saved as global rules.
import { get, post } from "../api.js";
import { $, createField, readFields, render, run } from "../ui.js";

const LABELS = {
  waves: ["Enemy waves", "Turn off for peaceful building."],
  waveTimer: ["Automatic wave timer", 'Off = waves only come when you press "Send next wave".'],
  waveSpacing: ["Time between waves (seconds)", ""],
  waitEnemies: ["Wait for enemies to die", "The next wave waits until the current one is cleared."],
  winWave: ["Win at wave", "0 = the game never ends by surviving waves."],
  infiniteResources: ["Infinite resources", "Build anything for free."],
  fog: ["Fog of war", ""],
  coreIncinerates: ["Core burns excess items", ""],
  unitCap: ["Extra unit cap", "Added to the normal unit limit."],
  buildSpeedMultiplier: ["Build speed ×", ""],
  buildCostMultiplier: ["Build cost ×", ""],
  unitBuildSpeedMultiplier: ["Unit production speed ×", ""],
  unitDamageMultiplier: ["Unit damage ×", ""],
  unitHealthMultiplier: ["Unit health ×", ""],
  blockHealthMultiplier: ["Block health ×", ""],
  blockDamageMultiplier: ["Block (turret) damage ×", ""],
  deconstructRefundMultiplier: ["Deconstruct refund ×", "1 = full refund."],
};

const PRESETS = {
  endless: { winWave: 0 },
  manual: { waveTimer: false, winWave: 0 },
  peaceful: { waves: false, winWave: 0 },
  chill: {
    waves: true,
    waveTimer: true,
    waveSpacing: 300,
    waitEnemies: true,
    buildSpeedMultiplier: 2,
    winWave: 0,
  },
  creative: { infiniteResources: true },
};

function fieldKind(type) {
  if (type === "seconds") {
    return "int";
  }
  return type;
}

export async function load() {
  try {
    const { live, types } = await get("/api/rules");
    const fields = Object.entries(types).map(([name, type]) => {
      const [label, help] = LABELS[name] || [name, ""];
      return createField({ name, kind: fieldKind(type), value: live[name], label, help });
    });
    render($("#rulesFields"), fields);
  } catch (error) {
    $("#rulesFields").textContent = error.message;
  }
}

async function apply(values, message) {
  await run(post("/api/rules", { values }), message);
  setTimeout(load, 300);
}

function applyForm(event) {
  event.preventDefault();
  apply(readFields($("#rulesFields")), "Rules applied");
}

function applyPreset(event) {
  const button = event.target.closest("button[data-preset]");
  if (button) {
    apply(PRESETS[button.dataset.preset], "Preset applied");
  }
}

function resetRules() {
  const question =
    "Remove all rule overrides? New maps use their own defaults again. " +
    "The running game keeps its rules until the map changes.";
  if (confirm(question)) {
    run(post("/api/rules/reset"), "Overrides removed");
  }
}

export function init() {
  $("#rulesForm").addEventListener("submit", applyForm);
  $("#presets").addEventListener("click", applyPreset);
  $("#resetRulesButton").addEventListener("click", resetRules);
}
