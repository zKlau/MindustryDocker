// App shell: login, tab switching and polling.
import { get, post } from "./api.js";
import { $, $$, toast } from "./ui.js";
import * as overview from "./tabs/overview.js";
import * as map from "./tabs/map.js";
import * as rules from "./tabs/rules.js";
import * as saves from "./tabs/saves.js";
import * as players from "./tabs/players.js";
import * as mods from "./tabs/mods.js";
import * as settings from "./tabs/settings.js";
import * as consoleTab from "./tabs/console.js";

const TABS = { overview, map, rules, saves, players, mods, settings, console: consoleTab };
const DEFAULT_TAB = "overview";

let started = false;
let loggedIn = false;

/** setInterval that pauses while logged out or while the browser tab is hidden. */
function every(milliseconds, callback) {
  setInterval(() => {
    if (loggedIn && !document.hidden) {
      callback();
    }
  }, milliseconds);
}

function activeTab() {
  return $("#tabs .active").dataset.tab;
}

function rememberTab(name) {
  try {
    localStorage.setItem("tab", name);
  } catch {
    // storage can be unavailable (private mode); remembering the tab is optional
  }
}

function savedTab() {
  try {
    const name = localStorage.getItem("tab");
    if (name in TABS) {
      return name;
    }
  } catch {
    // ignore, fall back to the default tab
  }
  return DEFAULT_TAB;
}

function showTab(name) {
  for (const button of $$("#tabs button")) {
    button.classList.toggle("active", button.dataset.tab === name);
  }
  for (const panel of $$(".tab-panel")) {
    panel.classList.toggle("active", panel.id === name);
  }
  TABS[name].load?.();
  rememberTab(name);
}

function showLogin() {
  loggedIn = false;
  $("#app").hidden = true;
  $("#login").hidden = false;
  $("#password").focus();
}

async function showServerName() {
  try {
    const { values } = await get("/api/config");
    if (values.name) {
      $("#title").textContent = values.name;
      document.title = `${values.name} · Admin`;
    }
  } catch {
    // keep the default title
  }
}

function startPolling() {
  overview.load();
  consoleTab.tail();
  every(5000, () => overview.load());
  every(1500, () => consoleTab.tail());
  every(5000, () => TABS[activeTab()].poll?.());
}

function showApp() {
  loggedIn = true;
  $("#login").hidden = true;
  $("#app").hidden = false;
  if (started) {
    return;
  }
  started = true;
  for (const tab of Object.values(TABS)) {
    tab.init?.();
  }
  showTab(savedTab());
  startPolling();
  showServerName();
}

async function login(event) {
  event.preventDefault();
  try {
    await post("/api/login", { password: $("#password").value });
    $("#password").value = "";
    showApp();
  } catch (error) {
    toast(error.message, true);
  }
}

async function logout() {
  await post("/api/logout").catch(() => {});
  location.reload();
}

async function checkSession() {
  try {
    const session = await get("/api/session");
    if (session.authed) {
      showApp();
      return;
    }
  } catch {
    // fall through to the login screen
  }
  showLogin();
}

$("#tabs").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-tab]");
  if (button) {
    showTab(button.dataset.tab);
  }
});
$("#loginForm").addEventListener("submit", login);
$("#logoutButton").addEventListener("click", logout);
window.addEventListener("logged-out", showLogin);

checkSession();
