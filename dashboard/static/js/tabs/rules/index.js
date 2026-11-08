import { get, post } from "../../api/client.js";
import { API } from "../../api/endpoints.js";
import { QUICK_REFRESH_MS } from "../../constants/timing.js";
import { $, onClick, render } from "../../ui/dom.js";
import { createField, readFields } from "../../ui/fields.js";
import { run } from "../../ui/toast.js";
import { LABELS, PRESETS } from "./constants.js";

function fieldKind(type) {
  if (type === "seconds") {
    return "int";
  }

  return type;
}

function createRuleField([name, type], live) {
  const [label, help] = LABELS[name] || [name, ""];

  return createField({ name, kind: fieldKind(type), value: live[name], label, help });
}

export async function load() {
  try {
    const { live, types } = await get(API.rules.current);
    render(
      $("#rulesFields"),
      Object.entries(types).map((rule) => createRuleField(rule, live)),
    );
  } catch (error) {
    $("#rulesFields").textContent = error.message;
  }
}

async function apply(values, message) {
  await run(post(API.rules.current, { values }), message);
  setTimeout(load, QUICK_REFRESH_MS);
}

function applyForm(event) {
  event.preventDefault();
  apply(readFields($("#rulesFields")), "Rules applied");
}

function resetRules() {
  const question =
    "Remove all rule overrides? New maps use their own defaults again. " +
    "The running game keeps its rules until the map changes.";
  if (confirm(question)) {
    run(post(API.rules.reset), "Overrides removed");
  }
}

export function init() {
  $("#rulesForm").addEventListener("submit", applyForm);
  onClick($("#presets"), "button[data-preset]", (button) =>
    apply(PRESETS[button.dataset.preset], "Preset applied"),
  );
  $("#resetRulesButton").addEventListener("click", resetRules);
}
