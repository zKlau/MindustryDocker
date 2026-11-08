import { get, post } from "../api/client.js";
import { API } from "../api/endpoints.js";
import { REFRESH_MS } from "../constants/timing.js";
import { store } from "../store.js";
import { setBadge } from "../ui/badges.js";
import { $, cloneTemplate, fillText, render } from "../ui/dom.js";
import { run } from "../ui/toast.js";
import { capitalize, formatDuration } from "../utils/format.js";

function pillState(status) {
  if (status.error) {
    return { text: "Starting…", className: "bad" };
  }
  if (!status.running) {
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
  setBadge($("#statePill"), text, `pill ${className}`);
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
    ["Played", formatDuration(status.minutes * 60)],
    ["Server FPS", status.fps],
    ["Memory", `${status.heapMB} MB`],
  ];
}

function createTile([label, value]) {
  const tile = cloneTemplate("tileTemplate");
  fillText(tile, { ".tile-label": label, ".tile-value": value });

  return tile;
}

function renderPauseButton(status) {
  if (status.paused) {
    $("#pauseButton").textContent = "Resume";
  } else {
    $("#pauseButton").textContent = "Pause";
  }
}

export async function load() {
  try {
    store.status = await get(API.status);
  } catch (error) {
    store.status = { running: false, error: error.message };
  }
  renderPill(store.status);
  render($("#tiles"), tileValues(store.status).map(createTile));
  renderPauseButton(store.status);
}

async function action(path, message, body) {
  await run(post(path, body), message);
  setTimeout(load, REFRESH_MS);
}

function togglePause() {
  if (store.status.paused) {
    action(API.game.pause, "Resumed", { on: false });
  } else {
    action(API.game.pause, "Paused", { on: true });
  }
}

function forceGameOver() {
  if (confirm("Force a game over? The next map will load.")) {
    action(API.game.gameOver, "Game over");
  }
}

function restartServer() {
  const message =
    "Restart the server? The game is saved first and continues after the restart " +
    '(if startup is set to "Continue the last game").';
  if (confirm(message)) {
    action(API.game.restart, "Restarting…");
  }
}

function broadcast(event) {
  event.preventDefault();
  const message = $("#sayMessage").value.trim();
  if (!message) {
    return;
  }
  run(post(API.game.say, { message }), "Sent");
  $("#sayMessage").value = "";
}

export function init() {
  $("#pauseButton").addEventListener("click", togglePause);
  $("#waveButton").addEventListener("click", () => action(API.game.nextWave, "Wave sent"));
  $("#fillButton").addEventListener("click", () => action(API.game.fillCore, "Core filled"));
  $("#gameOverButton").addEventListener("click", forceGameOver);
  $("#restartButton").addEventListener("click", restartServer);
  $("#sayForm").addEventListener("submit", broadcast);
}
