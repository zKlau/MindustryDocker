import { get, post } from "../../api/client.js";
import { API } from "../../api/endpoints.js";
import { REFRESH_MS } from "../../constants/timing.js";
import { $, cloneTemplate, fillText, onAction, render } from "../../ui/dom.js";
import { emptyRow, renderRows } from "../../ui/table.js";
import { run } from "../../ui/toast.js";
import * as access from "./access.js";

const PLAYERS_TABLE = { columns: 4, emptyText: "Nobody is online." };
const BANS_TABLE = { columns: 3, emptyText: "Nobody is banned." };

function adminButtonText(player) {
  if (player.admin) {
    return "Remove admin";
  }

  return "Make admin";
}

function createPlayerRow(player) {
  const row = cloneTemplate("playerRowTemplate");
  row.dataset.id = player.uuid;
  row.dataset.name = player.name;
  row.dataset.admin = String(player.admin);
  fillText(row, { ".player-name": player.name, ".player-team": player.team, ".player-ip": player.ip });
  row.querySelector(".player-admin").hidden = !player.admin;
  row.querySelector('[data-action="admin"]').textContent = adminButtonText(player);

  return row;
}

function createBanRow({ who, id, key }) {
  const row = cloneTemplate("banRowTemplate");
  row.dataset.id = key;
  fillText(row, { ".ban-who": who, ".ban-id": id });

  return row;
}

async function loadOnline() {
  renderRows($("#playerRows"), await get(API.players.online), createPlayerRow, PLAYERS_TABLE);
}

async function loadBans() {
  const { ids, ips } = await get(API.players.bans);
  const bans = [
    ...ids.map((ban) => ({ who: ban.name, id: ban.id, key: ban.id })),
    ...ips.map((ip) => ({ who: ip, id: "IP ban", key: ip })),
  ];
  renderRows($("#banRows"), bans, createBanRow, BANS_TABLE);
}

async function loadPlayers() {
  try {
    await Promise.all([loadOnline(), loadBans()]);
  } catch (error) {
    render($("#playerRows"), [emptyRow(PLAYERS_TABLE.columns, error.message)]);
  }
}

export function load() {
  loadPlayers();
  access.load();
}

export function poll() {
  loadPlayers();
  access.poll();
}

const ROW_ACTIONS = {
  admin: (row) => run(post(API.players.admin, { id: row.dataset.id, on: row.dataset.admin !== "true" })),
  kick: (row) => run(post(API.players.kick, { id: row.dataset.id }), "Kicked"),
  ban: (row) =>
    confirm(`Ban ${row.dataset.name}?`) && run(post(API.players.ban, { id: row.dataset.id }), "Banned"),
  unban: (row) => run(post(API.players.unban, { id: row.dataset.id }), "Unbanned"),
};

async function onRowAction(action, button) {
  const handler = ROW_ACTIONS[action];
  if (handler && (await handler(button.closest("tr")))) {
    setTimeout(loadPlayers, REFRESH_MS);
  }
}

export function init() {
  access.init();
  onAction($("#playerRows"), onRowAction);
  onAction($("#banRows"), onRowAction);
}
