// Online mods: search the official Mindustry mod list and install mods from GitHub.
import { get, post } from "../api.js";
import { $, cloneTemplate, emptyRow, fillText, render, run, toast } from "../ui.js";

const COLUMNS = 4;
const SEARCH_DELAY = 400;

let page = 0;
let loaded = false;
let searchTimer = null;
let onInstalled = () => {};

function kindText(mod) {
  if (mod.java) {
    return "Java";
  }
  return "Script / content";
}

function authorText(mod) {
  if (!mod.author) {
    return "";
  }
  return `by ${mod.author}`;
}

function createRow(mod) {
  const row = cloneTemplate("onlineModRowTemplate");
  row.dataset.repo = mod.repo;
  row.dataset.name = mod.name;
  fillText(row, {
    ".online-mod-name": mod.name,
    ".online-mod-author": authorText(mod),
    ".online-mod-kind": kindText(mod),
    ".online-mod-description": mod.description,
    ".online-mod-stars": `★ ${mod.stars}`,
    ".online-mod-version": mod.version,
  });
  row.querySelector(".online-mod-description").title = mod.description;
  const incompatible = row.querySelector(".online-mod-incompatible");
  incompatible.hidden = mod.compatible;
  incompatible.textContent = `needs build ${mod.minGameVersion}`;
  if (mod.installed) {
    row.querySelector("button").textContent = "Reinstall";
  }
  return row;
}

function searchUrl() {
  const params = new URLSearchParams({
    q: $("#onlineModSearch").value.trim(),
    sort: $("#onlineModSort").value,
    compatible: String(Number($("#onlineModCompatible").checked)),
    page: String(page),
  });
  return `/api/online/mods?${params}`;
}

function showTotal(result) {
  $("#onlineModSearch").placeholder = `Search ${result.total} mods`;
}

async function fetchPage({ append }) {
  const body = $("#onlineModRows");
  try {
    const result = await get(searchUrl());
    showTotal(result);
    const rows = result.mods.map(createRow);
    if (append) {
      body.append(...rows);
    } else if (rows.length === 0) {
      render(body, [emptyRow(COLUMNS, "No mods found.")]);
    } else {
      render(body, rows);
    }
    $("#onlineModsMore").hidden = !result.hasMore;
  } catch (error) {
    render(body, [emptyRow(COLUMNS, `The mod list is not reachable right now: ${error.message}`)]);
  }
}

function newSearch() {
  page = 0;
  fetchPage({ append: false });
}

function scheduleSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(newSearch, SEARCH_DELAY);
}

function loadMore() {
  page += 1;
  fetchPage({ append: true });
}

async function install(row, button) {
  button.disabled = true;
  button.textContent = "Installing…";
  const result = await run(post("/api/online/mods/install", { repo: row.dataset.repo }), null);
  button.disabled = false;
  if (!result) {
    button.textContent = "Install";
    return;
  }
  button.textContent = "Reinstall";
  toast(`Installed ${row.dataset.name}. Restart the server to load it.`);
  onInstalled();
}

function onRowClick(event) {
  const button = event.target.closest('button[data-action="install"]');
  if (button) {
    install(button.closest("tr"), button);
  }
}

/** Load the first page the first time the Mods tab is opened. */
export function load() {
  if (!loaded) {
    loaded = true;
    newSearch();
  }
}

export function init(afterInstall) {
  onInstalled = afterInstall;
  $("#onlineModForm").addEventListener("submit", (event) => event.preventDefault());
  $("#onlineModSearch").addEventListener("input", scheduleSearch);
  $("#onlineModSort").addEventListener("change", newSearch);
  $("#onlineModCompatible").addEventListener("change", newSearch);
  $("#onlineModsMore").addEventListener("click", loadMore);
  $("#onlineModRows").addEventListener("click", onRowClick);
}
