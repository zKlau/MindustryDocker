// Players: online list with kick/ban/admin, and the ban list.
import { get, post } from "../api.js";
import { $, cloneTemplate, emptyRow, fillText, render, run } from "../ui.js";
import * as access from "./access.js";

function createPlayerRow(player) {
  const row = cloneTemplate("playerRowTemplate");
  row.dataset.id = player.uuid;
  row.dataset.name = player.name;
  row.dataset.admin = String(player.admin);
  fillText(row, { ".player-name": player.name, ".player-team": player.team, ".player-ip": player.ip });
  row.querySelector(".player-admin").hidden = !player.admin;
  const adminButton = row.querySelector('[data-action="admin"]');
  if (player.admin) {
    adminButton.textContent = "Remove admin";
  } else {
    adminButton.textContent = "Make admin";
  }
  return row;
}

function createBanRow(who, id, key) {
  const row = cloneTemplate("banRowTemplate");
  row.dataset.id = key;
  fillText(row, { ".ban-who": who, ".ban-id": id });
  return row;
}

async function loadOnline() {
  const players = await get("/api/players");
  if (players.length === 0) {
    render($("#playerRows"), [emptyRow(4, "Nobody is online.")]);
    return;
  }
  render($("#playerRows"), players.map(createPlayerRow));
}

async function loadBans() {
  const { ids, ips } = await get("/api/players/bans");
  const rows = [
    ...ids.map((ban) => createBanRow(ban.name, ban.id, ban.id)),
    ...ips.map((ip) => createBanRow(ip, "IP ban", ip)),
  ];
  if (rows.length === 0) {
    render($("#banRows"), [emptyRow(3, "Nobody is banned.")]);
    return;
  }
  render($("#banRows"), rows);
}

async function loadPlayers() {
  try {
    await Promise.all([loadOnline(), loadBans()]);
  } catch (error) {
    render($("#playerRows"), [emptyRow(4, error.message)]);
  }
}

export function load() {
  loadPlayers();
  access.load();
}

/** Periodic refresh: lists only, so form controls being edited aren't overwritten. */
export function poll() {
  loadPlayers();
  access.poll();
}

function runAction(action, row) {
  const id = row.dataset.id;
  if (action === "admin") {
    return run(post("/api/players/admin", { id, on: row.dataset.admin !== "true" }));
  }
  if (action === "kick") {
    return run(post("/api/players/kick", { id }), "Kicked");
  }
  if (action === "ban" && confirm(`Ban ${row.dataset.name}?`)) {
    return run(post("/api/players/ban", { id }), "Banned");
  }
  if (action === "unban") {
    return run(post("/api/players/unban", { id }), "Unbanned");
  }
  return Promise.resolve(false);
}

async function onClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  if (await runAction(button.dataset.action, button.closest("tr"))) {
    setTimeout(loadPlayers, 400);
  }
}

export function init() {
  access.init();
  $("#playerRows").addEventListener("click", onClick);
  $("#banRows").addEventListener("click", onClick);
}
