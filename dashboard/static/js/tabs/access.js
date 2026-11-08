// Join protection on the Players tab: join password and whitelist.
import { get, post } from "../api.js";
import { $, cloneTemplate, emptyRow, fillText, render, run, toast } from "../ui.js";

let current = null;

function rememberedText(status) {
  if (!status.passwordEnabled) {
    return "The join password is off.";
  }
  if (status.rememberedCount === 1) {
    return "1 player has logged in and is remembered.";
  }
  return `${status.rememberedCount} players have logged in and are remembered.`;
}

function createRequestRow(request) {
  const row = cloneTemplate("requestRowTemplate");
  row.dataset.id = request.id;
  row.dataset.name = request.name;
  fillText(row, {
    ".request-name": request.name,
    ".request-id": request.id,
    ".request-time": new Date(request.time * 1000).toLocaleString(),
  });
  return row;
}

function createApprovedRow(player) {
  const row = cloneTemplate("approvedRowTemplate");
  row.dataset.id = player.id;
  row.dataset.name = player.name;
  fillText(row, { ".approved-name": player.name, ".approved-id": player.id });
  return row;
}

function renderRows(container, items, createRow, emptyMessage, columns) {
  if (items.length === 0) {
    render(container, [emptyRow(columns, emptyMessage)]);
    return;
  }
  render(container, items.map(createRow));
}

function renderControls(status) {
  $("#passwordEnabled").checked = status.passwordEnabled;
  $("#whitelistEnabled").checked = status.whitelistEnabled;
  $("#loginTimeout").textContent = status.loginTimeout;
}

function renderLists(status) {
  $("#rememberedInfo").textContent = rememberedText(status);
  renderRows($("#requestRows"), status.requests, createRequestRow, "Nobody is waiting.", 4);
  renderRows($("#approvedRows"), status.approved, createApprovedRow, "No approved players yet.", 3);
}

async function refresh({ controls }) {
  try {
    current = await get("/api/access");
    if (controls) {
      renderControls(current);
    }
    renderLists(current);
  } catch (error) {
    $("#rememberedInfo").textContent = error.message;
  }
}

export function load() {
  refresh({ controls: true });
}

export function poll() {
  refresh({ controls: false });
}

async function savePassword(event) {
  event.preventDefault();
  const enabled = $("#passwordEnabled").checked;
  const password = $("#joinPassword").value;
  if (enabled && !password && !current?.hasPassword) {
    toast("Type a password first", true);
    return;
  }
  const body = { enabled };
  if (password) {
    body.password = password;
  }
  if (await run(post("/api/access/password", body), "Join password saved")) {
    $("#joinPassword").value = "";
  }
  load();
}

async function forgetLogins() {
  const question =
    "Forget everyone who logged in? They will have to type the password again next time they join.";
  if (confirm(question)) {
    await run(post("/api/access/forget"), "Logins forgotten");
    load();
  }
}

async function toggleWhitelist() {
  const enabled = $("#whitelistEnabled").checked;
  let message = "Whitelist off";
  if (enabled) {
    message = "Whitelist on";
  }
  await run(post("/api/access/whitelist", { enabled }), message);
  load();
}

function runRowAction(action, row) {
  const body = { id: row.dataset.id, name: row.dataset.name };
  if (action === "approve") {
    return run(post("/api/access/whitelist/approve", body), `Approved ${row.dataset.name}`);
  }
  if (action === "dismiss") {
    return run(post("/api/access/whitelist/dismiss", body), null);
  }
  if (action === "remove" && confirm(`Remove ${row.dataset.name} from the whitelist?`)) {
    return run(post("/api/access/whitelist/remove", body), "Removed");
  }
  return Promise.resolve(false);
}

async function onRowClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  if (await runRowAction(button.dataset.action, button.closest("tr"))) {
    load();
  }
}

export function init() {
  $("#passwordForm").addEventListener("submit", savePassword);
  $("#forgetLoginsButton").addEventListener("click", forgetLogins);
  $("#whitelistEnabled").addEventListener("change", toggleWhitelist);
  $("#requestRows").addEventListener("click", onRowClick);
  $("#approvedRows").addEventListener("click", onRowClick);
}
