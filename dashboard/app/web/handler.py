"""HTTP request handler: serves the static frontend and dispatches /api/* to routes."""

import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler

from .. import settings
from ..server import log, server
from . import auth, routes  # noqa: F401  (importing routes registers them)
from .router import ApiError, Response, resolve

STATIC_ROOT = settings.STATIC_DIR.resolve()
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:"
    ),
}
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")


class Handler(BaseHTTPRequestHandler):
    server_version = "MindustryDashboard"

    def log_message(self, fmt, *args):  # keep container logs for the game
        pass

    # ------------------------------------------------------------ helpers

    def client_ip(self):
        forwarded = (
            self.headers.get("CF-Connecting-IP") or self.headers.get("X-Forwarded-For", "").split(",")[0]
        )
        return forwarded.strip() or self.client_address[0]

    def cookie(self, name):
        for part in self.headers.get("Cookie", "").split(";"):
            key, _, value = part.strip().partition("=")
            if key == name:
                return value
        return None

    def authed(self):
        return auth.valid(self.cookie(auth.COOKIE))

    def _send(self, status, body, content_type, headers=None):
        all_headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
            "Cache-Control": "no-store",
            **SECURITY_HEADERS,
            **(headers or {}),
        }
        self.send_response(status)
        for key, value in all_headers.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status, obj):
        self._send(status, json.dumps(obj).encode(), "application/json")

    # ------------------------------------------------------------ static files

    def _static(self, path):
        rel = urllib.parse.unquote(path).lstrip("/") or "index.html"
        target = (STATIC_ROOT / rel).resolve()
        if STATIC_ROOT not in target.parents or not target.is_file():
            target = STATIC_ROOT / "index.html"  # unknown paths fall back to the app
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/"):
            content_type += "; charset=utf-8"
        headers = {}
        if target.name != "index.html":
            headers["Cache-Control"] = "public, max-age=300"
        self._send(200, target.read_bytes(), content_type, headers)

    # ------------------------------------------------------------ dispatch

    def _rejection(self, method, entry):
        """An (status, message) pair if the request must be refused, else None."""
        if entry is None:
            return 404, "Not found"
        _, public = entry
        # CSRF guard: a cross-site form can't set custom headers.
        if method == "POST" and self.headers.get("X-Dashboard") != "1":
            return 400, "Bad request"
        if not public and not self.authed():
            return 401, "Unauthorized"
        return None

    def _call(self, fn, req):
        """Run a route and turn exceptions into (status, payload)."""
        try:
            return 200, fn(req)
        except ApiError as error:
            return error.status, {"error": str(error)}
        except ValueError as error:
            return 400, {"error": str(error)}
        except (RuntimeError, OSError) as error:
            return 503, {"error": str(error)}
        except Exception as error:  # noqa: BLE001 - never leave a request hanging
            log(f"error in {req.path}: {error!r}")
            return 500, {"error": "Internal error"}

    def _respond(self, status, result):
        if isinstance(result, Response):
            body = result.body
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
            self._send(result.status, body, result.content_type, result.headers)
            return
        if result is None:
            result = {"ok": True}
        self._json(status, result)

    def _api(self, method):
        entry, req = resolve(method, self.path)
        req.handler = self
        rejection = self._rejection(method, entry)
        if rejection is not None:
            status, message = rejection
            self._json(status, {"error": message})
            return
        fn, _ = entry
        status, result = self._call(fn, req)
        self._respond(status, result)

    def _health(self):
        if server.alive():
            self._json(200, {"ok": True})
        else:
            self._json(503, {"ok": False})

    # BaseHTTPRequestHandler calls these by name.

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/healthz":
            self._health()
        elif path.startswith("/api/"):
            self._api("GET")
        else:
            self._static(path)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path.startswith("/api/"):
            self._api("POST")
        else:
            self._json(404, {"error": "Not found"})
