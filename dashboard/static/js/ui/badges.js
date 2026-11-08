import { capitalize } from "../utils/format.js";

export function setBadge(element, text, className) {
  element.textContent = text;
  element.className = className;
}

export function setPlanetBadge(element, planet) {
  setBadge(element, capitalize(planet), `badge ${planet}`);
  element.hidden = !planet;
}
