import { $$, cloneTemplate, fillText } from "./dom.js";

const MAX_TEXT_LENGTH = 100;

function createSwitch(name, value) {
  const row = cloneTemplate("switchFieldTemplate");
  const input = row.querySelector("input");
  input.name = name;
  input.checked = Boolean(value);

  return row;
}

function configureInput(input, kind) {
  if (kind === "str") {
    input.type = "text";
    input.maxLength = MAX_TEXT_LENGTH;

    return;
  }
  input.type = "number";
  input.min = "0";
  input.step = "1";
  if (kind === "float") {
    input.step = "0.1";
  }
}

function createInput(name, kind, value) {
  const row = cloneTemplate("inputFieldTemplate");
  const input = row.querySelector("input");
  input.name = name;
  input.value = value ?? "";
  configureInput(input, kind);

  return row;
}

export function createField({ name, kind, value, label, help = "" }) {
  let row = null;
  if (kind === "bool") {
    row = createSwitch(name, value);
  } else {
    row = createInput(name, kind, value);
  }
  fillText(row, { ".field-label": label, ".field-help": help });

  return row;
}

function inputValue(input) {
  if (input.type === "checkbox") {
    return input.checked;
  }
  if (input.type === "number") {
    return Number(input.value);
  }

  return input.value;
}

export function readFields(container) {
  const values = {};
  for (const input of $$("input[name]", container)) {
    values[input.name] = inputValue(input);
  }

  return values;
}

export function createFields(labels, types, values) {
  return Object.entries(labels)
    .filter(([name]) => name in types)
    .map(([name, [label, help]]) =>
      createField({ name, kind: types[name], value: values[name], label, help }),
    );
}
