import { cloneTemplate, render } from "./dom.js";

export function emptyRow(columns, message) {
  const row = cloneTemplate("emptyRowTemplate");
  const cell = row.querySelector("td");
  cell.colSpan = columns;
  cell.textContent = message;

  return row;
}

export function emptyMessage(message) {
  const paragraph = document.createElement("p");
  paragraph.className = "empty";
  paragraph.textContent = message;

  return paragraph;
}

export function renderRows(body, items, createRow, { columns, emptyText }) {
  if (items.length === 0) {
    render(body, [emptyRow(columns, emptyText)]);

    return;
  }
  render(body, items.map(createRow));
}

export async function loadRows(body, fetchItems, createRow, table) {
  try {
    renderRows(body, await fetchItems(), createRow, table);
  } catch (error) {
    render(body, [emptyRow(table.columns, error.message)]);
  }
}
