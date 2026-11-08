import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

from ..common.log import log
from ..server import server
from . import auth, cookies, routes, static_files
from .constants import API_PREFIX, CSRF_HEADER, CSRF_VALUE, HEALTH_PATH, JSON_TYPE, NO_STORE, SECURITY_HEADERS
from .router import ApiError, Response


class Handler(BaseHTTPRequestHandler):
    server_version = "MindustryDashboard"

    def log_message(self, fmt, *args):
        pass

    def client_ip(self):
        forwarded = (
            self.headers.get("CF-Connecting-IP") or self.headers.get("X-Forwarded-For", "").split(",")[0]
        )

        return forwarded.strip() or self.client_address[0]

    def cookie(self, name):
        return cookies.parse(self.headers.get("Cookie"), name)

    def is_https(self):
        return self.headers.get("X-Forwarded-Proto") == "https"

    def authed(self):
        return auth.valid(self.cookie(auth.COOKIE))

    def _send(self, status, body, content_type, headers=None):
        all_headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
            "Cache-Control": NO_STORE,
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
        self._send(status, json.dumps(obj).encode(), JSON_TYPE)

    def _error(self, status, message):
        self._json(status, {"error": message})

    def _rejection(self, method, entry):
        if entry is None:
            return 404, "Not found"
        _, public = entry
        if method == "POST" and self.headers.get(CSRF_HEADER) != CSRF_VALUE:
            return 400, "Bad request"
        if not public and not self.authed():
            return 401, "Unauthorized"

        return None

    def _call(self, fn, req):
        try:
            return 200, fn(req)
        except ApiError as error:
            return error.status, {"error": str(error)}
        except ValueError as error:
            return 400, {"error": str(error)}
        except (RuntimeError, OSError) as error:
            return 503, {"error": str(error)}
        except Exception as error:
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
        entry, req = routes.resolve(method, self.path)
        req.handler = self
        rejection = self._rejection(method, entry)
        if rejection is not None:
            self._error(*rejection)

            return
        fn, _ = entry
        self._respond(*self._call(fn, req))

    def _health(self):
        if server.alive():
            self._json(200, {"ok": True})
        else:
            self._json(503, {"ok": False})

    def _path(self):
        return urllib.parse.urlparse(self.path).path

    def do_GET(self):
        path = self._path()
        if path == HEALTH_PATH:
            self._health()
        elif path.startswith(API_PREFIX):
            self._api("GET")
        else:
            self._send(200, *static_files.load(path))

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if self._path().startswith(API_PREFIX):
            self._api("POST")
        else:
            self._error(404, "Not found")
