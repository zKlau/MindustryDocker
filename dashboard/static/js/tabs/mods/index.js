import { get, post, upload } from "../../api/client.js";
import { API } from "../../api/endpoints.js";
import { setBadge } from "../../ui/badges.js";
import { $, cloneTemplate, fillText, onClick } from "../../ui/dom.js";
import { loadRows } from "../../ui/table.js";
import { run } from "../../ui/toast.js";
import { setupUploader } from "../../ui/uploader.js";
import { formatBytes } from "../../utils/format.js";
import * as onlineMods from "./online.js";

const TABLE = { columns: 4, emptyText: "No mods installed." };

function statusOf(mod) {
  if (mod.error) {
    return { text: "error", className: "badge bad" };
  }
  if (mod.loaded) {
    return { text: "loaded", className: "badge" };
  }

  return { text: "restart needed", className: "badge" };
}

function createRow(mod) {
  const row = cloneTemplate("modRowTemplate");
  row.dataset.file = mod.file;
  fillText(row, {
    ".mod-name": mod.name,
    ".mod-version": mod.version,
    ".mod-file": mod.file,
    ".mod-size": formatBytes(mod.size),
  });
  const { text, className } = statusOf(mod);
  setBadge(row.querySelector(".mod-status"), text, className);

  return row;
}

export function load() {
  onlineMods.load();

  return loadRows($("#modRows"), () => get(API.mods.list), createRow, TABLE);
}

async function deleteMod(button) {
  const file = button.closest("tr").dataset.file;
  if (!confirm(`Delete ${file}? It is removed after the next restart.`)) {
    return;
  }
  if (await run(post(API.mods.delete, { file }), "Deleted")) {
    load();
  }
}

export function init() {
  onlineMods.init(load);
  onClick($("#modRows"), 'button[data-action="delete"]', deleteMod);
  setupUploader($("#modFile"), $("#uploadModButton"), (file) => upload(API.mods.upload, file), load);
}
