import { get, post } from "../../api/client.js";
import { API, withQuery } from "../../api/endpoints.js";
import { $, cloneTemplate, fillText, onClick, render, whileDisabled } from "../../ui/dom.js";
import { emptyRow, renderRows } from "../../ui/table.js";
import { run, toast } from "../../ui/toast.js";
import { bindPagedSearch, createPagedSearch } from "../../utils/paged-search.js";

const TABLE = { columns: 4, emptyText: "No mods found." };
const INSTALL_LABEL = "Install";
const REINSTALL_LABEL = "Reinstall";

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
    row.querySelector("button").textContent = REINSTALL_LABEL;
  }

  return row;
}

function searchUrl(page) {
  return withQuery(API.onlineMods.search, {
    q: $("#onlineModSearch").value.trim(),
    sort: $("#onlineModSort").value,
    compatible: String(Number($("#onlineModCompatible").checked)),
    page: String(page),
  });
}

async function fetchPage({ page, append }) {
  const body = $("#onlineModRows");
  try {
    const result = await get(searchUrl(page));
    $("#onlineModSearch").placeholder = `Search ${result.total} mods`;
    if (append) {
      body.append(...result.mods.map(createRow));
    } else {
      renderRows(body, result.mods, createRow, TABLE);
    }
    $("#onlineModsMore").hidden = !result.hasMore;
  } catch (error) {
    render(body, [emptyRow(TABLE.columns, `The mod list is not reachable right now: ${error.message}`)]);
  }
}

const search = createPagedSearch(fetchPage);

async function install(button) {
  const row = button.closest("tr");
  button.textContent = "Installing…";
  const result = await whileDisabled([button], () =>
    run(post(API.onlineMods.install, { repo: row.dataset.repo }), null),
  );
  if (!result) {
    button.textContent = INSTALL_LABEL;

    return;
  }
  button.textContent = REINSTALL_LABEL;
  toast(`Installed ${row.dataset.name}. Restart the server to load it.`);
  onInstalled();
}

export function load() {
  search.loadOnce();
}

export function init(afterInstall) {
  onInstalled = afterInstall;
  bindPagedSearch(search, {
    form: $("#onlineModForm"),
    input: $("#onlineModSearch"),
    filters: [$("#onlineModSort"), $("#onlineModCompatible")],
    moreButton: $("#onlineModsMore"),
  });
  onClick($("#onlineModRows"), 'button[data-action="install"]', install);
}
