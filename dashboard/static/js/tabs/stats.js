import { get, post } from "../api/client.js";
import { API } from "../api/endpoints.js";
import { $, $$, cloneTemplate, fillText, onClick, render } from "../ui/dom.js";
import { emptyRow, renderRows } from "../ui/table.js";
import { run } from "../ui/toast.js";
import { formatDate, formatDuration } from "../utils/format.js";

const TABLE = { columns: 9, emptyText: "No stats yet. They appear after players have been online." };
const DEFAULT_SORT = "playtime";
const NAME_SORT = "name";

let players = [];
let sortKey = DEFAULT_SORT;
let ascending = false;

function formatLastSeen(player) {
  if (player.online) {
    return "now";
  }

  return formatDate(player.lastSeen);
}

function compare(a, b) {
  if (sortKey === NAME_SORT) {
    return a.name.localeCompare(b.name);
  }

  return a[sortKey] - b[sortKey];
}

function sortedPlayers() {
  const query = $("#statsSearch").value.trim().toLowerCase();
  const visible = players.filter((player) => player.name.toLowerCase().includes(query));
  visible.sort(compare);
  if (!ascending) {
    visible.reverse();
  }

  return visible;
}

function createRow(player, index) {
  const row = cloneTemplate("statsRowTemplate");
  row.dataset.id = player.id;
  row.dataset.name = player.name;
  fillText(row, {
    ".stats-rank": String(index + 1),
    ".stats-name": player.name || player.id,
    ".stats-playtime": formatDuration(player.playtime),
    ".stats-sessions": String(player.sessions),
    ".stats-built": String(player.built),
    ".stats-broken": String(player.broken),
    ".stats-waves": String(player.waves),
    ".stats-last-seen": formatLastSeen(player),
  });
  row.querySelector(".stats-online").hidden = !player.online;

  return row;
}

function renderTable() {
  renderRows($("#statsRows"), sortedPlayers(), createRow, TABLE);
}

function renderSortButtons() {
  for (const button of $$(".sort-button")) {
    const active = button.dataset.sort === sortKey;
    button.classList.toggle("active", active);
    button.classList.toggle("ascending", active && ascending);
  }
}

export async function load() {
  try {
    const result = await get(API.stats.leaderboard);
    players = result.players;
    renderTable();
  } catch (error) {
    render($("#statsRows"), [emptyRow(TABLE.columns, error.message)]);
  }
}

export const poll = load;

function changeSort(button) {
  if (button.dataset.sort === sortKey) {
    ascending = !ascending;
  } else {
    sortKey = button.dataset.sort;
    ascending = sortKey === NAME_SORT;
  }
  renderSortButtons();
  renderTable();
}

async function removePlayer(button) {
  const row = button.closest("tr");
  if (!confirm(`Remove the stats of ${row.dataset.name}?`)) {
    return;
  }
  if (await run(post(API.stats.remove, { id: row.dataset.id }), "Removed")) {
    load();
  }
}

async function resetAll() {
  if (!confirm("Reset the stats of every player? This can't be undone.")) {
    return;
  }
  if (await run(post(API.stats.reset), "Stats reset")) {
    load();
  }
}

export function init() {
  onClick($(".stats-table thead"), ".sort-button", changeSort);
  onClick($("#statsRows"), 'button[data-action="remove"]', removePlayer);
  $("#statsSearch").addEventListener("input", renderTable);
  $("#resetStatsButton").addEventListener("click", resetAll);
}
