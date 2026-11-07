// Map: pick a custom/built-in map or campaign sector (any planet), with previews, and play it.
import { get, post, previewUrl, upload } from "../api.js";
import {
  $,
  $$,
  capitalize,
  cloneTemplate,
  fillText,
  render,
  run,
  setPlanetBadge,
  setupUploader,
} from "../ui.js";
import { store } from "../store.js";

let catalog = { maps: [], sectors: [] };
let planetFilter = "";

function toEntry(kind, item) {
  if (kind === "sector") {
    return {
      kind,
      name: item.id,
      label: item.name,
      planet: item.planet,
      custom: false,
      w: item.w,
      h: item.h,
    };
  }
  return {
    kind,
    name: item.name,
    label: item.name,
    planet: item.planet,
    custom: item.custom,
    w: item.w,
    h: item.h,
  };
}

function matchesFilters(entry) {
  const query = $("#mapSearch").value.trim().toLowerCase();
  if (planetFilter && entry.planet !== planetFilter) {
    return false;
  }
  return !query || entry.label.toLowerCase().includes(query);
}

function groups() {
  const maps = catalog.maps.map((item) => toEntry("map", item));
  const sectors = catalog.sectors.map((item) => toEntry("sector", item));
  return [
    { title: "Uploaded maps", entries: maps.filter((m) => m.custom) },
    { title: "Custom game maps", entries: maps.filter((m) => !m.custom) },
    { title: "Campaign sectors", entries: sectors },
  ]
    .map((group) => ({ ...group, entries: group.entries.filter(matchesFilters) }))
    .filter((group) => group.entries.length > 0);
}

function isSelected(entry) {
  const selected = store.selectedMap;
  return Boolean(selected) && selected.kind === entry.kind && selected.name === entry.name;
}

function createCard(entry) {
  const card = cloneTemplate("mapCardTemplate");
  card.dataset.kind = entry.kind;
  card.dataset.name = entry.name;
  card.classList.toggle("selected", isSelected(entry));
  card.querySelector(".map-preview").src = previewUrl(entry.kind, entry.name);
  fillText(card, { ".map-name": entry.label, ".map-size": `${entry.w}×${entry.h}` });
  setPlanetBadge(card.querySelector(".map-planet"), entry.planet);
  return card;
}

function createGroup(group) {
  const element = cloneTemplate("mapGroupTemplate");
  element.querySelector(".map-group-title").textContent = group.title;
  render(element.querySelector(".map-grid"), group.entries.map(createCard));
  return element;
}

function renderMaps() {
  const visible = groups();
  if (visible.length === 0) {
    const message = document.createElement("p");
    message.className = "empty";
    message.textContent = "No maps match.";
    render($("#mapGroups"), [message]);
    return;
  }
  render($("#mapGroups"), visible.map(createGroup));
}

function renderSelection() {
  const entry = store.selectedMap;
  const preview = $("#selectedMapPreview");
  $("#hostButton").disabled = !entry;
  $("#nextButton").disabled = !entry || entry.kind !== "map";
  $("#deleteMapButton").hidden = !entry || !entry.custom;
  preview.hidden = !entry;
  if (!entry) {
    $("#selectedMapName").textContent = "No map selected";
    $("#selectedMapInfo").textContent = "Click a map above.";
    return;
  }
  preview.src = previewUrl(entry.kind, entry.name);
  $("#selectedMapName").textContent = entry.label;
  $("#selectedMapInfo").textContent = selectionInfo(entry);
}

function selectionInfo(entry) {
  const planet = capitalize(entry.planet);
  if (entry.kind === "sector") {
    return `Campaign sector on ${planet}, ${entry.w}×${entry.h}. Sectors can only be played right away.`;
  }
  return `Map on ${planet}, ${entry.w}×${entry.h}.`;
}

export async function load() {
  try {
    catalog = await get("/api/maps");
    renderMaps();
    renderSelection();
  } catch (error) {
    const message = document.createElement("p");
    message.className = "empty";
    message.textContent = error.message;
    render($("#mapGroups"), [message]);
  }
}

function selectCard(event) {
  const card = event.target.closest(".map-card");
  if (!card) {
    return;
  }
  const all = groups().flatMap((group) => group.entries);
  store.selectedMap = all.find((e) => e.kind === card.dataset.kind && e.name === card.dataset.name) || null;
  for (const other of $$("#mapGroups .map-card")) {
    other.classList.toggle("selected", other === card);
  }
  renderSelection();
}

function choosePlanet(event) {
  const button = event.target.closest("button[data-planet]");
  if (!button) {
    return;
  }
  planetFilter = button.dataset.planet;
  for (const other of $$("#planetFilter button")) {
    other.classList.toggle("active", other === button);
  }
  renderMaps();
}

async function hostSelected() {
  const entry = store.selectedMap;
  const question = `Play ${entry.label} now? The current game is replaced (save it first to keep it).`;
  if (!confirm(question)) {
    return;
  }
  $("#hostButton").disabled = true;
  const body = { kind: entry.kind, name: entry.name, mode: $("#modeSelect").value };
  await run(post("/api/maps/host", body), "Map loaded");
  $("#hostButton").disabled = false;
}

function playNext() {
  run(post("/api/maps/next", { name: store.selectedMap.name }), "Will play after this game ends");
}

async function deleteSelected() {
  const entry = store.selectedMap;
  if (!confirm(`Delete the uploaded map ${entry.label}?`)) {
    return;
  }
  if (await run(post("/api/maps/delete", { name: entry.name }), "Deleted")) {
    store.selectedMap = null;
    setTimeout(load, 500);
  }
}

export function init() {
  $("#planetFilter").addEventListener("click", choosePlanet);
  $("#mapSearch").addEventListener("input", renderMaps);
  $("#mapGroups").addEventListener("click", selectCard);
  $("#hostButton").addEventListener("click", hostSelected);
  $("#nextButton").addEventListener("click", playNext);
  $("#deleteMapButton").addEventListener("click", deleteSelected);
  setupUploader(
    $("#mapFile"),
    $("#uploadMapButton"),
    (file) => upload("/api/maps/upload", file),
    () => setTimeout(load, 800),
  );
}
