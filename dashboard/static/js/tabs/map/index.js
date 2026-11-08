import { get, post, upload } from "../../api/client.js";
import { API } from "../../api/endpoints.js";
import { REFRESH_MS, SLOW_REFRESH_MS } from "../../constants/timing.js";
import { store } from "../../store.js";
import { $, $$, onClick, setActive, whileDisabled } from "../../ui/dom.js";
import { run } from "../../ui/toast.js";
import { setupUploader } from "../../ui/uploader.js";
import { groups, sameEntry, setCatalog } from "./entries.js";
import * as onlineMaps from "./online.js";
import { renderGroups, renderMessage, renderSelection } from "./render.js";

let planetFilter = "";

function visibleGroups() {
  return groups({ query: $("#mapSearch").value.trim().toLowerCase(), planet: planetFilter });
}

function renderMaps() {
  renderGroups(visibleGroups());
}

export async function load() {
  onlineMaps.load();
  try {
    setCatalog(await get(API.maps.list));
    renderMaps();
    renderSelection();
  } catch (error) {
    renderMessage(error.message);
  }
}

function reloadSoon() {
  setTimeout(load, SLOW_REFRESH_MS);
}

function selectCard(card) {
  const clicked = { kind: card.dataset.kind, name: card.dataset.name };
  const all = visibleGroups().flatMap((group) => group.entries);
  store.selectedMap = all.find((entry) => sameEntry(entry, clicked)) || null;
  setActive($$("#mapGroups .map-card"), (other) => other === card, "selected");
  renderSelection();
}

function choosePlanet(button) {
  planetFilter = button.dataset.planet;
  setActive($$("#planetFilter button"), (other) => other === button);
  renderMaps();
}

async function hostSelected() {
  const entry = store.selectedMap;
  const question = `Play ${entry.label} now? The current game is replaced (save it first to keep it).`;
  if (!confirm(question)) {
    return;
  }
  const body = { kind: entry.kind, name: entry.name, mode: $("#modeSelect").value };
  await whileDisabled([$("#hostButton")], () => run(post(API.maps.host, body), "Map loaded"));
}

function playNext() {
  run(post(API.maps.next, { name: store.selectedMap.name }), "Will play after this game ends");
}

async function deleteSelected() {
  const entry = store.selectedMap;
  if (!confirm(`Delete the uploaded map ${entry.label}?`)) {
    return;
  }
  if (await run(post(API.maps.delete, { name: entry.name }), "Deleted")) {
    store.selectedMap = null;
    setTimeout(load, REFRESH_MS);
  }
}

export function init() {
  onlineMaps.init(reloadSoon);
  onClick($("#planetFilter"), "button[data-planet]", choosePlanet);
  onClick($("#mapGroups"), ".map-card", selectCard);
  $("#mapSearch").addEventListener("input", renderMaps);
  $("#hostButton").addEventListener("click", hostSelected);
  $("#nextButton").addEventListener("click", playNext);
  $("#deleteMapButton").addEventListener("click", deleteSelected);
  setupUploader($("#mapFile"), $("#uploadMapButton"), (file) => upload(API.maps.upload, file), reloadSoon);
}
