import { get, post } from "../../api/client.js";
import { API } from "../../api/endpoints.js";
import { $, cloneTemplate, fillText, onAction } from "../../ui/dom.js";
import { renderRows } from "../../ui/table.js";
import { run, toast } from "../../ui/toast.js";
import { formatDate } from "../../utils/format.js";

const REQUESTS_TABLE = { columns: 4, emptyText: "Nobody is waiting." };
const APPROVED_TABLE = { columns: 3, emptyText: "No approved players yet." };

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

function createPlayerRow(templateId, player, texts) {
  const row = cloneTemplate(templateId);
  row.dataset.id = player.id;
  row.dataset.name = player.name;
  fillText(row, texts);

  return row;
}

function createRequestRow(request) {
  return createPlayerRow("requestRowTemplate", request, {
    ".request-name": request.name,
    ".request-id": request.id,
    ".request-time": formatDate(request.time),
  });
}

function createApprovedRow(player) {
  return createPlayerRow("approvedRowTemplate", player, {
    ".approved-name": player.name,
    ".approved-id": player.id,
  });
}

function renderControls(status) {
  $("#passwordEnabled").checked = status.passwordEnabled;
  $("#whitelistEnabled").checked = status.whitelistEnabled;
  $("#loginTimeout").textContent = status.loginTimeout;
}

function renderLists(status) {
  $("#rememberedInfo").textContent = rememberedText(status);
  renderRows($("#requestRows"), status.requests, createRequestRow, REQUESTS_TABLE);
  renderRows($("#approvedRows"), status.approved, createApprovedRow, APPROVED_TABLE);
}

async function refresh({ controls }) {
  try {
    current = await get(API.access.status);
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
  if (await run(post(API.access.password, body), "Join password saved")) {
    $("#joinPassword").value = "";
  }
  load();
}

async function forgetLogins() {
  const question =
    "Forget everyone who logged in? They will have to type the password again next time they join.";
  if (confirm(question)) {
    await run(post(API.access.forget), "Logins forgotten");
    load();
  }
}

function whitelistMessage(enabled) {
  if (enabled) {
    return "Whitelist on";
  }

  return "Whitelist off";
}

async function toggleWhitelist() {
  const enabled = $("#whitelistEnabled").checked;
  await run(post(API.access.whitelist, { enabled }), whitelistMessage(enabled));
  load();
}

function playerOf(row) {
  return { id: row.dataset.id, name: row.dataset.name };
}

const ROW_ACTIONS = {
  approve: (row) => run(post(API.access.approve, playerOf(row)), `Approved ${row.dataset.name}`),
  dismiss: (row) => run(post(API.access.dismiss, playerOf(row)), null),
  remove: (row) =>
    confirm(`Remove ${row.dataset.name} from the whitelist?`) &&
    run(post(API.access.remove, playerOf(row)), "Removed"),
};

async function onRowAction(action, button) {
  const handler = ROW_ACTIONS[action];
  if (handler && (await handler(button.closest("tr")))) {
    load();
  }
}

export function init() {
  $("#passwordForm").addEventListener("submit", savePassword);
  $("#forgetLoginsButton").addEventListener("click", forgetLogins);
  $("#whitelistEnabled").addEventListener("change", toggleWhitelist);
  onAction($("#requestRows"), onRowAction);
  onAction($("#approvedRows"), onRowAction);
}
