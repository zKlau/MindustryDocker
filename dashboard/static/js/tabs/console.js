import { get, post } from "../api/client.js";
import { API, withQuery } from "../api/endpoints.js";
import { QUICK_REFRESH_MS } from "../constants/timing.js";
import { $, cloneTemplate } from "../ui/dom.js";
import { run } from "../ui/toast.js";

const MAX_LINES = 2000;
const STICKY_DISTANCE = 60;
const LEVEL_CLASSES = [
  ["[E]", "error"],
  ["[W]", "warn"],
];

const history = [];
let historyIndex = 0;
let lastSeq = 0;

function isNearBottom(element) {
  return element.scrollHeight - element.scrollTop - element.clientHeight < STICKY_DISTANCE;
}

function createLine(text) {
  const line = cloneTemplate("logLineTemplate");
  line.textContent = text;
  const level = LEVEL_CLASSES.find(([tag]) => text.includes(tag));
  if (level) {
    line.classList.add(level[1]);
  }

  return line;
}

function appendLines(lines) {
  const log = $("#log");
  const stick = isNearBottom(log);
  log.append(...lines.map((line) => createLine(line.t)));
  while (log.childElementCount > MAX_LINES) {
    log.firstElementChild.remove();
  }
  if (stick) {
    log.scrollTop = log.scrollHeight;
  }
}

function clearLog() {
  $("#log").replaceChildren();
  lastSeq = 0;
}

export async function tail() {
  const result = await get(withQuery(API.logs, { since: lastSeq })).catch(() => null);
  if (!result) {
    return;
  }
  const dashboardRestarted = result.last < lastSeq;
  if (dashboardRestarted) {
    clearLog();

    return;
  }
  if (result.lines.length > 0) {
    appendLines(result.lines);
  }
  lastSeq = result.last;
}

export function load() {
  const log = $("#log");
  log.scrollTop = log.scrollHeight;
  $("#commandInput").focus();
}

async function sendCommand(event) {
  event.preventDefault();
  const input = $("#commandInput");
  const command = input.value.trim();
  if (!command) {
    return;
  }
  history.push(command);
  historyIndex = history.length;
  input.value = "";
  if (await run(post(API.console, { command }), null)) {
    setTimeout(tail, QUICK_REFRESH_MS);
  }
}

function browseHistory(event) {
  const input = $("#commandInput");
  if (event.key === "ArrowUp" && historyIndex > 0) {
    historyIndex -= 1;
    input.value = history[historyIndex];
    event.preventDefault();
  } else if (event.key === "ArrowDown") {
    historyIndex = Math.min(history.length, historyIndex + 1);
    input.value = history[historyIndex] || "";
  }
}

export function init() {
  $("#commandForm").addEventListener("submit", sendCommand);
  $("#commandInput").addEventListener("keydown", browseHistory);
}
