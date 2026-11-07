// Online maps: search MindustryTool and install maps onto the server.
import { get, post } from "../api.js";
import { $, cloneTemplate, fillText, run, toast } from "../ui.js";

const SEARCH_DELAY = 400;

let page = 0;
let loaded = false;
let searchTimer = null;
let onInstalled = () => {};

function previewSource(id) {
  return `/api/online/maps/preview?id=${encodeURIComponent(id)}`;
}

function statsText(map) {
  return `♥ ${map.likes} · ${map.downloads} downloads`;
}

function createCard(map) {
  const card = cloneTemplate("onlineMapCardTemplate");
  card.dataset.id = map.id;
  card.dataset.name = map.name;
  card.querySelector(".map-preview").src = previewSource(map.id);
  fillText(card, { ".map-name": map.name, ".online-map-stats": statsText(map) });
  return card;
}

function showStatus(message) {
  const status = $("#onlineMapsStatus");
  status.textContent = message;
  status.hidden = !message;
}

function searchUrl() {
  const params = new URLSearchParams({
    q: $("#onlineMapSearch").value.trim(),
    sort: $("#onlineMapSort").value,
    page: String(page),
  });
  return `/api/online/maps?${params}`;
}

async function fetchPage({ append }) {
  showStatus("Loading…");
  try {
    const result = await get(searchUrl());
    const cards = result.maps.map(createCard);
    if (append) {
      $("#onlineMaps").append(...cards);
    } else {
      $("#onlineMaps").replaceChildren(...cards);
    }
    $("#onlineMapsMore").hidden = !result.hasMore;
    if ($("#onlineMaps").childElementCount === 0) {
      showStatus("No maps found.");
    } else {
      showStatus("");
    }
  } catch (error) {
    showStatus(`MindustryTool is not reachable right now: ${error.message}`);
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

function setButtonsDisabled(card, disabled) {
  for (const button of card.querySelectorAll("button")) {
    button.disabled = disabled;
  }
}

async function install(card, play) {
  const body = { id: card.dataset.id, play, mode: $("#onlineMapMode").value };
  if (play && !confirm(`Install and play ${card.dataset.name} now? The current game is replaced.`)) {
    return;
  }
  setButtonsDisabled(card, true);
  const result = await run(post("/api/online/maps/install", body), null);
  setButtonsDisabled(card, false);
  if (!result) {
    return;
  }
  if (play) {
    toast(`Now playing ${result.name}`);
  } else {
    toast(`Installed ${result.name}`);
  }
  onInstalled();
}

function onCardClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  install(button.closest(".online-map"), button.dataset.action === "play");
}

/** Load the first page the first time the Map tab is opened. */
export function load() {
  if (!loaded) {
    loaded = true;
    newSearch();
  }
}

export function init(afterInstall) {
  onInstalled = afterInstall;
  $("#onlineMapForm").addEventListener("submit", (event) => event.preventDefault());
  $("#onlineMapSearch").addEventListener("input", scheduleSearch);
  $("#onlineMapSort").addEventListener("change", newSearch);
  $("#onlineMapsMore").addEventListener("click", loadMore);
  $("#onlineMaps").addEventListener("click", onCardClick);
}
