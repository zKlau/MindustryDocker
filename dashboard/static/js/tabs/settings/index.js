import { get, post } from "../../api/client.js";
import { API } from "../../api/endpoints.js";
import { REFRESH_MS } from "../../constants/timing.js";
import { store } from "../../store.js";
import { $, $$, render } from "../../ui/dom.js";
import { createFields, readFields } from "../../ui/fields.js";
import { run, toast } from "../../ui/toast.js";
import { LABELS } from "./constants.js";

const MODE_MAP = "map";

function resumeText(startup) {
  if (startup.resumeSave) {
    return `Will load "${startup.resumeSave}" (the newest of the shutdown save and autosaves).`;
  }

  return "No save yet, so it falls back to MINDUSTRY_START_COMMANDS until the first shutdown.";
}

function startupMapText(startup) {
  if (startup.mode === MODE_MAP && startup.map) {
    return `Current: ${startup.map} (${startup.gamemode})`;
  }

  return "";
}

async function loadStartup() {
  const startup = await get(API.startup);
  for (const radio of $$("#startupForm input[name=mode]")) {
    radio.checked = radio.value === startup.mode;
  }
  $("#resumeInfo").textContent = resumeText(startup);
  $("#startupMap").textContent = startupMapText(startup);
}

async function loadConfig() {
  const { values, types } = await get(API.config);
  render($("#configFields"), createFields(LABELS, types, values));
}

export async function load() {
  try {
    await Promise.all([loadStartup(), loadConfig()]);
  } catch (error) {
    $("#configFields").textContent = error.message;
  }
}

function startupRequest() {
  const checked = $("#startupForm input[name=mode]:checked");
  if (!checked) {
    return null;
  }
  if (checked.value !== MODE_MAP) {
    return { mode: checked.value };
  }
  const selected = store.selectedMap;
  if (!selected) {
    toast("Select a map on the Map tab first", true);

    return null;
  }

  return { mode: MODE_MAP, kind: selected.kind, map: selected.name, gamemode: $("#modeSelect").value };
}

async function saveStartup(event) {
  event.preventDefault();
  const body = startupRequest();
  if (!body) {
    return;
  }
  if (await run(post(API.startup, body), "Startup behaviour saved")) {
    loadStartup();
  }
}

async function saveConfig(event) {
  event.preventDefault();
  const values = readFields($("#configFields"));
  if (await run(post(API.config, { values }), "Settings saved")) {
    setTimeout(loadConfig, REFRESH_MS);
  }
}

export function init() {
  $("#startupForm").addEventListener("submit", saveStartup);
  $("#configForm").addEventListener("submit", saveConfig);
}
