// DOM helpers shared by all tabs.

export function $(selector, root = document) {
  return root.querySelector(selector);
}

export function $$(selector, root = document) {
  return [...root.querySelectorAll(selector)];
}

/** Clone the first element of a <template id="..."> from index.html. */
export function cloneTemplate(id) {
  return document.getElementById(id).content.firstElementChild.cloneNode(true);
}

/** Set the text of several child elements at once: fillText(row, { ".name": "Bob" }). */
export function fillText(root, values) {
  for (const [selector, text] of Object.entries(values)) {
    root.querySelector(selector).textContent = text;
  }
}

/** Replace a container's children. */
export function render(container, elements) {
  container.replaceChildren(...elements);
}

/** A full-width table row with a message, for empty lists and errors. */
export function emptyRow(columns, message) {
  const row = cloneTemplate("emptyRowTemplate");
  const cell = row.querySelector("td");
  cell.colSpan = columns;
  cell.textContent = message;
  return row;
}

export function toast(message, isError = false) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  element.classList.toggle("error", isError);
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.classList.remove("show"), 2800);
}

/** Await an API call and show a toast. Returns the result, or false if it failed. */
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

export function capitalize(text) {
  if (!text) {
    return "";
  }
  return text[0].toUpperCase() + text.slice(1);
}

export function formatBytes(bytes) {
  if (bytes > 1048576) {
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function setPlanetBadge(element, planet) {
  element.textContent = capitalize(planet);
  element.className = `badge ${planet}`;
  element.hidden = !planet;
}

/** A labelled settings row: a switch for "bool", otherwise a text or number input. */
export function createField({ name, kind, value, label, help = "" }) {
  if (kind === "bool") {
    const row = cloneTemplate("switchFieldTemplate");
    const input = row.querySelector("input");
    input.name = name;
    input.checked = Boolean(value);
    fillText(row, { ".field-label": label, ".field-help": help });
    return row;
  }
  const row = cloneTemplate("inputFieldTemplate");
  const input = row.querySelector("input");
  input.name = name;
  input.value = value ?? "";
  if (kind === "str") {
    input.type = "text";
    input.maxLength = 100;
  } else {
    input.type = "number";
    input.min = "0";
    input.step = "1";
  }
  if (kind === "float") {
    input.step = "0.1";
  }
  fillText(row, { ".field-label": label, ".field-help": help });
  return row;
}

/** Read inputs created by createField() back into an object. */
export function readFields(container) {
  const values = {};
  for (const input of $$("input[name]", container)) {
    if (input.type === "checkbox") {
      values[input.name] = input.checked;
    } else if (input.type === "number") {
      values[input.name] = Number(input.value);
    } else {
      values[input.name] = input.value;
    }
  }
  return values;
}

/** Wire a file input and an upload button. */
export function setupUploader(fileInput, button, send, onDone) {
  button.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) {
      toast("Choose a file first", true);
      return;
    }
    button.disabled = true;
    const ok = await run(send(file), "Uploaded");
    button.disabled = false;
    if (ok) {
      fileInput.value = "";
      onDone();
    }
  });
}
