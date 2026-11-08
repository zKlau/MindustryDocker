// Stats: sortable player leaderboard.
import { get, post } from "../api.js";
import { $, $$, cloneTemplate, emptyRow, fillText, render, run } from "../ui.js";

const COLUMNS = 9;

let players = [];
let sortKey = "playtime";
let ascending = false;

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

function formatLastSeen(player) {
  if (player.online) {
    return "now";
  }
  return new Date(player.lastSeen * 1000).toLocaleString();
}

function compare(a, b) {
  if (sortKey === "name") {
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
  const visible = sortedPlayers();
  if (visible.length === 0) {
    render($("#statsRows"), [emptyRow(COLUMNS, "No stats yet. They appear after players have been online.")]);
    return;
  }
  render($("#statsRows"), visible.map(createRow));
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
    const result = await get("/api/stats");
    players = result.players;
    renderTable();
  } catch (error) {
    render($("#statsRows"), [emptyRow(COLUMNS, error.message)]);
  }
}

export const poll = load;

function changeSort(event) {
  const button = event.target.closest(".sort-button");
  if (!button) {
    return;
  }
  if (button.dataset.sort === sortKey) {
    ascending = !ascending;
  } else {
    sortKey = button.dataset.sort;
    ascending = sortKey === "name";
  }
  renderSortButtons();
  renderTable();
}

async function removePlayer(event) {
  const button = event.target.closest('button[data-action="remove"]');
  if (!button) {
    return;
  }
  const row = button.closest("tr");
  if (!confirm(`Remove the stats of ${row.dataset.name}?`)) {
    return;
  }
  if (await run(post("/api/stats/remove", { id: row.dataset.id }), "Removed")) {
    load();
  }
}

async function resetAll() {
  if (!confirm("Reset the stats of every player? This can't be undone.")) {
    return;
  }
  if (await run(post("/api/stats/reset"), "Stats reset")) {
    load();
  }
}

export function init() {
  $(".stats-table thead").addEventListener("click", changeSort);
  $("#statsSearch").addEventListener("input", renderTable);
  $("#statsRows").addEventListener("click", removePlayer);
  $("#resetStatsButton").addEventListener("click", resetAll);
}
