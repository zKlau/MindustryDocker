// Settings: startup behaviour and server config.
import { get, post } from "../api.js";
import { $, $$, createField, readFields, render, run, toast } from "../ui.js";
import { store } from "../store.js";

const LABELS = {
  name: ["Server name", ""],
  desc: ["Description", "Shown under the name in the server list."],
  motd: ["Message of the day", "Shown to players when they join."],
  playerLimit: ["Player limit", "0 = no limit."],
  autosave: ["Autosave", "Regular automatic backups of the running game."],
  autosaveSpacing: ["Autosave every (seconds)", ""],
  autosaveAmount: ["Autosaves to keep", ""],
  autoPause: ["Pause when nobody is online", ""],
  roundExtraTime: ["Seconds before next map after game over", ""],
  enableVotekick: ["Allow vote-kick", ""],
  showConnectMessages: ["Show join/leave messages", ""],
  antiSpam: ["Anti-spam", ""],
};

function resumeText(startup) {
  if (startup.resumeSave) {
    return `Will load "${startup.resumeSave}" (the newest of the shutdown save and autosaves).`;
  }
  return "No save yet, so it falls back to MINDUSTRY_START_COMMANDS until the first shutdown.";
}

function startupMapText(startup) {
  if (startup.mode === "map" && startup.map) {
    return `Current: ${startup.map} (${startup.gamemode})`;
  }
  return "";
}

async function loadStartup() {
  const startup = await get("/api/startup");
  for (const radio of $$("#startupForm input[name=mode]")) {
    radio.checked = radio.value === startup.mode;
  }
  $("#resumeInfo").textContent = resumeText(startup);
  $("#startupMap").textContent = startupMapText(startup);
}

async function loadConfig() {
  const { values, types } = await get("/api/config");
  const fields = Object.entries(LABELS)
    .filter(([name]) => name in types)
    .map(([name, [label, help]]) =>
      createField({ name, kind: types[name], value: values[name], label, help }),
    );
  render($("#configFields"), fields);
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
  if (checked.value !== "map") {
    return { mode: checked.value };
  }
  const selected = store.selectedMap;
  if (!selected) {
    toast("Select a map on the Map tab first", true);
    return null;
  }
  return { mode: "map", kind: selected.kind, map: selected.name, gamemode: $("#modeSelect").value };
}

async function saveStartup(event) {
  event.preventDefault();
  const body = startupRequest();
  if (!body) {
    return;
  }
  if (await run(post("/api/startup", body), "Startup behaviour saved")) {
    loadStartup();
  }
}

async function saveConfig(event) {
  event.preventDefault();
  const values = readFields($("#configFields"));
  if (await run(post("/api/config", { values }), "Settings saved")) {
    setTimeout(loadConfig, 500);
  }
}

export function init() {
  $("#startupForm").addEventListener("submit", saveStartup);
  $("#configForm").addEventListener("submit", saveConfig);
}
