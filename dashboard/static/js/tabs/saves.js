import { get, post, upload } from "../api/client.js";
import { API, saveDownloadUrl } from "../api/endpoints.js";
import { SLOW_REFRESH_MS } from "../constants/timing.js";
import { $, cloneTemplate, fillText, onAction } from "../ui/dom.js";
import { loadRows } from "../ui/table.js";
import { run } from "../ui/toast.js";
import { setupUploader } from "../ui/uploader.js";
import { formatBytes, formatDate } from "../utils/format.js";

const TABLE = { columns: 4, emptyText: "No saves yet." };

function createRow(save) {
  const row = cloneTemplate("saveRowTemplate");
  row.dataset.name = save.name;
  fillText(row, {
    ".save-name": save.name,
    ".save-date": formatDate(save.mtime),
    ".save-size": formatBytes(save.size),
  });
  row.querySelector(".save-auto").hidden = !save.auto;
  row.querySelector(".save-download").href = saveDownloadUrl(save.name);

  return row;
}

export function load() {
  return loadRows($("#saveRows"), () => get(API.saves.list), createRow, TABLE);
}

async function saveGame(event) {
  event.preventDefault();
  const name = $("#saveName").value.trim();
  if (!name) {
    return;
  }
  if (await run(post(API.saves.save, { name }), "Saved")) {
    setTimeout(load, SLOW_REFRESH_MS);
  }
}

async function loadSave(name) {
  if (confirm(`Load "${name}"? The current game is replaced.`)) {
    await run(post(API.saves.load, { name }), "Loading save…");
  }
}

async function deleteSave(name) {
  if (!confirm(`Delete "${name}" permanently?`)) {
    return;
  }
  if (await run(post(API.saves.delete, { name }), "Deleted")) {
    load();
  }
}

const ROW_ACTIONS = { load: loadSave, delete: deleteSave };

export function init() {
  $("#saveForm").addEventListener("submit", saveGame);
  onAction($("#saveRows"), (action, button) => ROW_ACTIONS[action]?.(button.closest("tr").dataset.name));
  setupUploader($("#saveFile"), $("#uploadSaveButton"), (file) => upload(API.saves.upload, file), load);
}
