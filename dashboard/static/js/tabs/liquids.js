import { $, cloneTemplate, render, setStatusText } from "../ui/dom.js";
import { formatCount } from "../utils/format.js";
import { setIcon } from "./resources.js";

const ICON_DIR = "/img/liquids";
const RATE_EPSILON = 0.05;
const DECIMAL_LIMIT = 10;

function formatRate(value) {
  if (value < DECIMAL_LIMIT) {
    return `${Number(value.toFixed(1))}/s`;
  }

  return `${formatCount(Math.round(value))}/s`;
}

function netClass(liquid) {
  const net = liquid.produced - liquid.used;
  if (net >= RATE_EPSILON) {
    return "up";
  }
  if (net <= -RATE_EPSILON) {
    return "down";
  }

  return "";
}

function flowText(liquid) {
  return `+${formatRate(liquid.produced)} · −${formatRate(liquid.used)}`;
}

function createLiquid(liquid) {
  const element = cloneTemplate("resourceTemplate");
  setIcon(element, `${ICON_DIR}/${liquid.name}.png`, liquid.color);
  element.title = `${liquid.label}: ${formatRate(liquid.produced)} made, ${formatRate(liquid.used)} used`;
  $(".resource-amount", element).textContent = formatCount(Math.round(liquid.stored));
  const rate = $(".resource-rate", element);
  rate.textContent = flowText(liquid);
  rate.className = `resource-rate ${netClass(liquid)}`;

  return element;
}

export function renderLiquids(status) {
  const liquids = status.hosting && status.liquids;
  $("#liquidsCard").hidden = !liquids || liquids.length === 0;
  if (!liquids) {
    return;
  }
  setStatusText(
    $("#liquidsHint"),
    "Stored in all tanks, conduits and machines. Per second: estimated made by pumps, extractors and factories, and used by machines (turret coolant not counted).",
  );
  render($("#liquids"), liquids.map(createLiquid));
}
