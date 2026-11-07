// Mods: list, upload and delete mod/plugin files.
import { get, post, upload } from "../api.js";
import { $, cloneTemplate, emptyRow, fillText, formatBytes, render, run, setupUploader } from "../ui.js";
import * as onlineMods from "./online-mods.js";

const COLUMNS = 4;

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
  const status = statusOf(mod);
  const badge = row.querySelector(".mod-status");
  badge.textContent = status.text;
  badge.className = status.className;
  return row;
}

export async function load() {
  onlineMods.load();
  const body = $("#modRows");
  try {
    const mods = await get("/api/mods");
    if (mods.length === 0) {
      render(body, [emptyRow(COLUMNS, "No mods installed.")]);
      return;
    }
    render(body, mods.map(createRow));
  } catch (error) {
    render(body, [emptyRow(COLUMNS, error.message)]);
  }
}

async function onClick(event) {
  const button = event.target.closest('button[data-action="delete"]');
  if (!button) {
    return;
  }
  const file = button.closest("tr").dataset.file;
  if (!confirm(`Delete ${file}? It is removed after the next restart.`)) {
    return;
  }
  if (await run(post("/api/mods/delete", { file }), "Deleted")) {
    load();
  }
}

export function init() {
  onlineMods.init(load);
  $("#modRows").addEventListener("click", onClick);
  setupUploader($("#modFile"), $("#uploadModButton"), (file) => upload("/api/mods/upload", file), load);
}
