import { mapPreviewUrl } from "../../api/endpoints.js";
import { store } from "../../store.js";
import { setPlanetBadge } from "../../ui/badges.js";
import { $, cloneTemplate, fillText, render } from "../../ui/dom.js";
import { emptyMessage } from "../../ui/table.js";
import { capitalize } from "../../utils/format.js";
import { isSelected, KIND_MAP, KIND_SECTOR } from "./entries.js";

function sizeText(entry) {
  return `${entry.w}×${entry.h}`;
}

function createCard(entry) {
  const card = cloneTemplate("mapCardTemplate");
  card.dataset.kind = entry.kind;
  card.dataset.name = entry.name;
  card.classList.toggle("selected", isSelected(entry));
  card.querySelector(".map-preview").src = mapPreviewUrl(entry.kind, entry.name);
  fillText(card, { ".map-name": entry.label, ".map-size": sizeText(entry) });
  setPlanetBadge(card.querySelector(".map-planet"), entry.planet);

  return card;
}

function createGroup(group) {
  const element = cloneTemplate("mapGroupTemplate");
  element.querySelector(".map-group-title").textContent = group.title;
  render(element.querySelector(".map-grid"), group.entries.map(createCard));

  return element;
}

export function renderGroups(groups) {
  if (groups.length === 0) {
    renderMessage("No maps match.");

    return;
  }
  render($("#mapGroups"), groups.map(createGroup));
}

export function renderMessage(message) {
  render($("#mapGroups"), [emptyMessage(message)]);
}

function selectionInfo(entry) {
  const planet = capitalize(entry.planet);
  if (entry.kind === KIND_SECTOR) {
    return `Campaign sector on ${planet}, ${sizeText(entry)}. Sectors can only be played right away.`;
  }

  return `Map on ${planet}, ${sizeText(entry)}.`;
}

export function renderSelection() {
  const entry = store.selectedMap;
  const preview = $("#selectedMapPreview");
  $("#hostButton").disabled = !entry;
  $("#nextButton").disabled = !entry || entry.kind !== KIND_MAP;
  $("#deleteMapButton").hidden = !entry || !entry.custom;
  preview.hidden = !entry;
  if (!entry) {
    $("#selectedMapName").textContent = "No map selected";
    $("#selectedMapInfo").textContent = "Click a map above.";

    return;
  }
  preview.src = mapPreviewUrl(entry.kind, entry.name);
  $("#selectedMapName").textContent = entry.label;
  $("#selectedMapInfo").textContent = selectionInfo(entry);
}
