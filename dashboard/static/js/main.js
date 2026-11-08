import { get } from "./api/client.js";
import { API } from "./api/endpoints.js";
import { LOG_POLL_MS, STATUS_POLL_MS, TAB_POLL_MS } from "./constants/timing.js";
import { every } from "./shell/polling.js";
import { startSession } from "./shell/session.js";
import { activeTab, setupTabs, startTabs } from "./shell/tabs.js";
import * as consoleTab from "./tabs/console.js";
import * as map from "./tabs/map/index.js";
import * as mods from "./tabs/mods/index.js";
import * as overview from "./tabs/overview.js";
import * as players from "./tabs/players/index.js";
import * as rules from "./tabs/rules/index.js";
import * as saves from "./tabs/saves.js";
import * as settings from "./tabs/settings/index.js";
import * as stats from "./tabs/stats.js";
import { $ } from "./ui/dom.js";

const TABS = { overview, map, rules, saves, players, stats, mods, settings, console: consoleTab };
const DEFAULT_TAB = "overview";

function startPolling() {
  overview.load();
  consoleTab.tail();
  every(STATUS_POLL_MS, () => overview.load());
  every(LOG_POLL_MS, () => consoleTab.tail());
  every(TAB_POLL_MS, () => activeTab().poll?.());
}

async function showServerName() {
  const config = await get(API.config).catch(() => ({ values: {} }));
  const name = config.values.name;
  if (name) {
    $("#title").textContent = name;
    document.title = `${name} · Admin`;
  }
}

function startApp() {
  startTabs();
  startPolling();
  showServerName();
}

setupTabs(TABS, DEFAULT_TAB);
startSession(startApp);
