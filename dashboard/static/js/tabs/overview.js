// Overview: live status tiles and quick actions.
import { get, post } from "../api.js";
import { $, capitalize, cloneTemplate, fillText, render, run } from "../ui.js";
import { store } from "../store.js";

function pillState(status) {
  if (!status.running || status.error) {
    if (status.error) {
      return { text: "Starting…", className: "bad" };
    }
    return { text: "Offline", className: "bad" };
  }
  if (!status.hosting) {
    return { text: "Not hosting", className: "" };
  }
  if (status.paused) {
    return { text: "Paused", className: "" };
  }
  return { text: "Online", className: "ok" };
}

function renderPill(status) {
  const { text, className } = pillState(status);
  const pill = $("#statePill");
  pill.textContent = text;
  pill.className = `pill ${className}`;
}

function waveText(status) {
  if (status.winWave > 0) {
    return `${status.wave} / ${status.winWave}`;
  }
  return String(status.wave);
}

function nextWaveText(status) {
  if (status.waveTimer) {
    return `${status.nextWave}s`;
  }
  return "Manual";
}

function playerText(status) {
  const limit = status.playerLimit || "∞";
  return `${status.players} / ${limit}`;
}

function tileValues(status) {
  if (!status.hosting) {
    return [["Status", status.error || "No game running. Pick a map on the Map tab."]];
  }
  return [
    ["Map", status.map],
    ["Planet", capitalize(status.planet)],
    ["Mode", capitalize(status.mode)],
    ["Wave", waveText(status)],
    ["Next wave", nextWaveText(status)],
    ["Players", playerText(status)],
    ["Enemies", status.enemies],
    ["Played", `${Math.floor(status.minutes / 60)}h ${status.minutes % 60}m`],
    ["Server FPS", status.fps],
    ["Memory", `${status.heapMB} MB`],
  ];
}

function renderTiles(status) {
  const tiles = tileValues(status).map(([label, value]) => {
    const tile = cloneTemplate("tileTemplate");
    fillText(tile, { ".tile-label": label, ".tile-value": value });
    return tile;
  });
  render($("#tiles"), tiles);
}

export async function load() {
  try {
    store.status = await get("/api/status");
  } catch (error) {
    store.status = { running: false, error: error.message };
  }
  renderPill(store.status);
  renderTiles(store.status);
  if (store.status.paused) {
    $("#pauseButton").textContent = "Resume";
  } else {
    $("#pauseButton").textContent = "Pause";
  }
}

async function action(path, message, body) {
  await run(post(path, body), message);
  setTimeout(load, 600);
}

function togglePause() {
  if (store.status.paused) {
    action("/api/game/pause", "Resumed", { on: false });
  } else {
    action("/api/game/pause", "Paused", { on: true });
  }
}

function forceGameOver() {
  if (confirm("Force a game over? The next map will load.")) {
    action("/api/game/game-over", "Game over");
  }
}

function restartServer() {
  const message =
    "Restart the server? The game is saved first and continues after the restart " +
    '(if startup is set to "Continue the last game").';
  if (confirm(message)) {
    action("/api/game/restart", "Restarting…");
  }
}

function broadcast(event) {
  event.preventDefault();
  const message = $("#sayMessage").value.trim();
  if (!message) {
    return;
  }
  run(post("/api/game/say", { message }), "Sent");
  $("#sayMessage").value = "";
}

export function init() {
  $("#pauseButton").addEventListener("click", togglePause);
  $("#waveButton").addEventListener("click", () => action("/api/game/next-wave", "Wave sent"));
  $("#fillButton").addEventListener("click", () => action("/api/game/fill-core", "Core filled"));
  $("#gameOverButton").addEventListener("click", forceGameOver);
  $("#restartButton").addEventListener("click", restartServer);
  $("#sayForm").addEventListener("submit", broadcast);
}
