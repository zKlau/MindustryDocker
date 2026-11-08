import { get, post } from "../../api/client.js";
import { API, onlineMapPreviewUrl, withQuery } from "../../api/endpoints.js";
import { $, $$, cloneTemplate, fillText, onAction, setStatusText, whileDisabled } from "../../ui/dom.js";
import { run, toast } from "../../ui/toast.js";
import { bindPagedSearch, createPagedSearch } from "../../utils/paged-search.js";

let onInstalled = () => {};

function createCard(map) {
  const card = cloneTemplate("onlineMapCardTemplate");
  card.dataset.id = map.id;
  card.dataset.name = map.name;
  card.querySelector(".map-preview").src = onlineMapPreviewUrl(map.id);
  fillText(card, {
    ".map-name": map.name,
    ".online-map-stats": `♥ ${map.likes} · ${map.downloads} downloads`,
  });

  return card;
}

function showStatus(message) {
  setStatusText($("#onlineMapsStatus"), message);
}

function searchUrl(page) {
  return withQuery(API.onlineMaps.search, {
    q: $("#onlineMapSearch").value.trim(),
    sort: $("#onlineMapSort").value,
    page: String(page),
  });
}

function showCards(cards, append) {
  const grid = $("#onlineMaps");
  if (append) {
    grid.append(...cards);
  } else {
    grid.replaceChildren(...cards);
  }
  if (grid.childElementCount === 0) {
    showStatus("No maps found.");
  } else {
    showStatus("");
  }
}

async function fetchPage({ page, append }) {
  showStatus("Loading…");
  try {
    const result = await get(searchUrl(page));
    showCards(result.maps.map(createCard), append);
    $("#onlineMapsMore").hidden = !result.hasMore;
  } catch (error) {
    showStatus(`MindustryTool is not reachable right now: ${error.message}`);
  }
}

const search = createPagedSearch(fetchPage);

function installedMessage(name, play) {
  if (play) {
    return `Now playing ${name}`;
  }

  return `Installed ${name}`;
}

async function install(card, play) {
  if (play && !confirm(`Install and play ${card.dataset.name} now? The current game is replaced.`)) {
    return;
  }
  const body = { id: card.dataset.id, play, mode: $("#onlineMapMode").value };
  const result = await whileDisabled($$("button", card), () => run(post(API.onlineMaps.install, body), null));
  if (result) {
    toast(installedMessage(result.name, play));
    onInstalled();
  }
}

export function load() {
  search.loadOnce();
}

export function init(afterInstall) {
  onInstalled = afterInstall;
  bindPagedSearch(search, {
    form: $("#onlineMapForm"),
    input: $("#onlineMapSearch"),
    filters: [$("#onlineMapSort")],
    moreButton: $("#onlineMapsMore"),
  });
  onAction($("#onlineMaps"), (action, button) => install(button.closest(".online-map"), action === "play"));
}
