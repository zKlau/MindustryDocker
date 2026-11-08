import { $, cloneTemplate, render, setStatusText } from "../ui/dom.js";
import { formatCount } from "../utils/format.js";

const ICON_DIR = "/img/power";
const BALANCE_EPSILON = 0.05;

function perSecond(value) {
  return `${formatCount(Math.round(value))}/s`;
}

function balanceTile(balance) {
  if (balance >= BALANCE_EPSILON) {
    return { icon: "diode", value: `+${perSecond(balance)}`, caption: "Balance", className: "up" };
  }
  if (balance <= -BALANCE_EPSILON) {
    return { icon: "diode", value: `−${perSecond(-balance)}`, caption: "Balance", className: "down" };
  }

  return { icon: "diode", value: "0/s", caption: "Balance", className: "" };
}

function tiles(power) {
  return [
    {
      icon: "battery",
      value: `${formatCount(Math.round(power.stored))} / ${formatCount(Math.round(power.capacity))}`,
      caption: "Stored",
      className: "",
    },
    { icon: "combustion-generator", value: perSecond(power.produced), caption: "Generated", className: "" },
    { icon: "power-node", value: perSecond(power.needed), caption: "Used", className: "" },
    balanceTile(power.balance),
  ];
}

function createTile(tile) {
  const element = cloneTemplate("resourceTemplate");
  $("img", element).src = `${ICON_DIR}/${tile.icon}.png`;
  const value = $(".resource-amount", element);
  value.textContent = tile.value;
  value.classList.add(...tile.className.split(" ").filter(Boolean));
  $(".resource-rate", element).textContent = tile.caption;

  return element;
}

function networkText(count) {
  if (count === 1) {
    return "1 network";
  }

  return `${count} networks`;
}

function hintText(power) {
  const total = `Totals across ${networkText(power.networks)}.`;
  if (power.short > 0) {
    return `${total} ⚠ ${power.short} of ${power.networks} short on power.`;
  }

  return total;
}

export function renderPower(status) {
  const power = status.hosting && status.power;
  $("#powerCard").hidden = !power;
  if (!power) {
    return;
  }
  const hint = $("#powerHint");
  setStatusText(hint, hintText(power));
  hint.classList.toggle("warning", power.short > 0);
  render($("#power"), tiles(power).map(createTile));
}
