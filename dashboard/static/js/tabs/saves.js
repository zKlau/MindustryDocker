// Saves: save, load, download, upload and delete saved games.
import { get, post, upload } from "../api.js";
import { $, cloneTemplate, emptyRow, fillText, formatBytes, render, run, setupUploader } from "../ui.js";

const COLUMNS = 4;

function createRow(save) {
  const row = cloneTemplate("saveRowTemplate");
  row.dataset.name = save.name;
  fillText(row, {
    ".save-name": save.name,
    ".save-date": new Date(save.mtime * 1000).toLocaleString(),
    ".save-size": formatBytes(save.size),
  });
  row.querySelector(".save-auto").hidden = !save.auto;
  row.querySelector(".save-download").href = `/api/saves/download?name=${encodeURIComponent(save.name)}`;
  return row;
}

export async function load() {
  const body = $("#saveRows");
  try {
    const saves = await get("/api/saves");
    if (saves.length === 0) {
      render(body, [emptyRow(COLUMNS, "No saves yet.")]);
      return;
    }
    render(body, saves.map(createRow));
  } catch (error) {
    render(body, [emptyRow(COLUMNS, error.message)]);
  }
}

async function saveGame(event) {
  event.preventDefault();
  const name = $("#saveName").value.trim();
  if (!name) {
    return;
  }
  if (await run(post("/api/saves/save", { name }), "Saved")) {
    setTimeout(load, 800);
  }
}

async function loadSave(name) {
  if (confirm(`Load "${name}"? The current game is replaced.`)) {
    await run(post("/api/saves/load", { name }), "Loading save…");
  }
}

async function deleteSave(name) {
  if (!confirm(`Delete "${name}" permanently?`)) {
    return;
  }
  if (await run(post("/api/saves/delete", { name }), "Deleted")) {
    load();
  }
}

function onRowClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  const name = button.closest("tr").dataset.name;
  if (button.dataset.action === "load") {
    loadSave(name);
  } else if (button.dataset.action === "delete") {
    deleteSave(name);
  }
}

export function init() {
  $("#saveForm").addEventListener("submit", saveGame);
  $("#saveRows").addEventListener("click", onRowClick);
  setupUploader($("#saveFile"), $("#uploadSaveButton"), (file) => upload("/api/saves/upload", file), load);
}
