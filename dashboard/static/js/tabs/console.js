// Console: live server log and a command box with history.
import { get, post } from "../api.js";
import { $, cloneTemplate, run } from "../ui.js";

const MAX_LINES = 2000;
const STICKY_DISTANCE = 60;

const history = [];
let historyIndex = 0;
let lastSeq = 0;

function isNearBottom(element) {
  return element.scrollHeight - element.scrollTop - element.clientHeight < STICKY_DISTANCE;
}

function createLine(text) {
  const line = cloneTemplate("logLineTemplate");
  line.textContent = text;
  if (text.includes("[E]")) {
    line.classList.add("error");
  } else if (text.includes("[W]")) {
    line.classList.add("warn");
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

export async function tail() {
  try {
    const { lines, last } = await get(`/api/logs?since=${lastSeq}`);
    if (last < lastSeq) {
      // the dashboard restarted and its log buffer starts over
      $("#log").replaceChildren();
      lastSeq = 0;
      return;
    }
    if (lines.length > 0) {
      appendLines(lines);
    }
    lastSeq = last;
  } catch {
    // the status pill already shows connection problems
  }
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
  if (await run(post("/api/console", { command }), null)) {
    setTimeout(tail, 300);
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
