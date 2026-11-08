import { withQuery } from "./endpoints.js";

const CSRF_HEADERS = { "X-Dashboard": "1" };
const UNAUTHORIZED = 401;

export const LOGGED_OUT_EVENT = "logged-out";

async function handle(response) {
  if (response.status === UNAUTHORIZED) {
    window.dispatchEvent(new Event(LOGGED_OUT_EVENT));
    throw new Error("Please log in again");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || response.statusText);
  }

  return data;
}

export function get(path) {
  return fetch(path).then(handle);
}

export function post(path, body = {}) {
  return fetch(path, {
    method: "POST",
    headers: { ...CSRF_HEADERS, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(handle);
}

export function upload(path, file) {
  return fetch(withQuery(path, { name: file.name }), {
    method: "POST",
    headers: CSRF_HEADERS,
    body: file,
  }).then(handle);
}
