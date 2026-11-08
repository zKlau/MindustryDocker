import { $, cloneTemplate, render, setStatusText } from "../ui/dom.js";
import { formatCount } from "../utils/format.js";

const ICON_DIR = "/img/items";
const RATE_EPSILON = 0.05;

function isShown(item) {
  return item.amount > 0 || Math.abs(item.rate || 0) >= RATE_EPSILON;
}

function rateState(rate) {
  if (rate === null || rate === undefined) {
    return { text: "measuring…", className: "" };
  }
  if (rate >= RATE_EPSILON) {
    return { text: `+${formatCount(Number(rate.toFixed(1)))}/s`, className: "up" };
  }
  if (rate <= -RATE_EPSILON) {
    return { text: `−${formatCount(Number((-rate).toFixed(1)))}/s`, className: "down" };
  }

  return { text: "0/s", className: "" };
}

function showSwatch(icon, color) {
  icon.replaceChildren();
  icon.style.background = `#${color}`;
}

function createResource(item) {
  const element = cloneTemplate("resourceTemplate");
  const icon = $(".resource-icon", element);
  const image = $("img", icon);
  image.addEventListener("error", () => showSwatch(icon, item.color));
  image.src = `${ICON_DIR}/${item.name}.png`;
  element.title = item.label;
  $(".resource-amount", element).textContent = formatCount(item.amount);
  const { text, className } = rateState(item.rate);
  const rate = $(".resource-rate", element);
  rate.textContent = text;
  rate.className = `resource-rate ${className}`;

  return element;
}

function hintText(core, shown) {
  if (shown.length === 0) {
    return "The core is empty.";
  }

  return `Items in your team's core (capacity ${formatCount(core.capacity)} each). Rates are net change per second over the last 30 game seconds.`;
}

export function renderResources(status) {
  const core = status.hosting && status.core;
  $("#resourcesCard").hidden = !core;
  if (!core) {
    return;
  }
  const shown = core.items.filter(isShown);
  setStatusText($("#resourcesHint"), hintText(core, shown));
  render($("#resources"), shown.map(createResource));
}
