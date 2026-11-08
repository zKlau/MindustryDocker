import { $, $$, onClick, setActive } from "../ui/dom.js";
import { readStorage, writeStorage } from "../utils/storage.js";

const STORAGE_KEY = "tab";

let tabs = {};
let defaultTab = "";

export function activeTab() {
  return tabs[$("#tabs .active").dataset.tab];
}

function savedTab() {
  const name = readStorage(STORAGE_KEY);
  if (name in tabs) {
    return name;
  }

  return defaultTab;
}

export function showTab(name) {
  setActive($$("#tabs button"), (button) => button.dataset.tab === name);
  setActive($$(".tab-panel"), (panel) => panel.id === name);
  tabs[name].load?.();
  writeStorage(STORAGE_KEY, name);
}

export function setupTabs(modules, fallback) {
  tabs = modules;
  defaultTab = fallback;
  onClick($("#tabs"), "button[data-tab]", (button) => showTab(button.dataset.tab));
}

export function startTabs() {
  for (const tab of Object.values(tabs)) {
    tab.init?.();
  }
  showTab(savedTab());
}
