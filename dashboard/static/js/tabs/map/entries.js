import { store } from "../../store.js";

export const KIND_MAP = "map";
export const KIND_SECTOR = "sector";

let catalog = { maps: [], sectors: [] };

export function setCatalog(value) {
  catalog = value;
}

function mapEntry(item) {
  return {
    kind: KIND_MAP,
    name: item.name,
    label: item.name,
    planet: item.planet,
    custom: item.custom,
    w: item.w,
    h: item.h,
  };
}

function sectorEntry(item) {
  return {
    kind: KIND_SECTOR,
    name: item.id,
    label: item.name,
    planet: item.planet,
    custom: false,
    w: item.w,
    h: item.h,
  };
}

function matches(entry, { query, planet }) {
  if (planet && entry.planet !== planet) {
    return false;
  }

  return !query || entry.label.toLowerCase().includes(query);
}

export function groups(filter) {
  const maps = catalog.maps.map(mapEntry);

  return [
    { title: "Uploaded maps", entries: maps.filter((m) => m.custom) },
    { title: "Custom game maps", entries: maps.filter((m) => !m.custom) },
    { title: "Campaign sectors", entries: catalog.sectors.map(sectorEntry) },
  ]
    .map((group) => ({ ...group, entries: group.entries.filter((entry) => matches(entry, filter)) }))
    .filter((group) => group.entries.length > 0);
}

export function sameEntry(a, b) {
  return Boolean(a) && Boolean(b) && a.kind === b.kind && a.name === b.name;
}

export function isSelected(entry) {
  return sameEntry(store.selectedMap, entry);
}
