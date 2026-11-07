// Small fetch wrapper for the dashboard API.

const HEADERS = { "X-Dashboard": "1" };

async function handle(response) {
  if (response.status === 401) {
    window.dispatchEvent(new Event("logged-out"));
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
    headers: { ...HEADERS, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(handle);
}

export function upload(path, file) {
  const url = `${path}?name=${encodeURIComponent(file.name)}`;
  return fetch(url, { method: "POST", headers: HEADERS, body: file }).then(handle);
}

/** URL of a map preview image (served as PNG, cached by the server). */
export function previewUrl(kind, name) {
  const params = new URLSearchParams({ kind, name });
  return `/api/maps/preview?${params}`;
}
