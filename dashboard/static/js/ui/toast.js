import { TOAST_MS } from "../constants/timing.js";
import { $ } from "./dom.js";

let hideTimer = null;

export function toast(message, isError = false) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  element.classList.toggle("error", isError);
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => element.classList.remove("show"), TOAST_MS);
}

export async function run(promise, okMessage = "Done") {
  try {
    const result = await promise;
    if (okMessage) {
      toast(okMessage);
    }

    return result ?? true;
  } catch (error) {
    toast(error.message, true);

    return false;
  }
}
