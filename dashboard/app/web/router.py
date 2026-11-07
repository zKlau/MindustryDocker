"""A tiny route table: `@route("GET", "/api/x")` registers a handler taking a Request."""

import json
import urllib.parse

_routes = {}


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Request:
    def __init__(self, handler, path, query):
        self.handler = handler
        self.path = path
        self.query = query

    def arg(self, name, default=""):
        return self.query.get(name, [default])[0]

    def body(self, limit=64 * 1024):
        length = int(self.handler.headers.get("Content-Length") or 0)
        if length > limit:
            raise ApiError(413, "Upload is too large")
        if length == 0:
            return b""
        return self.handler.rfile.read(length)

    def json(self):
        try:
            data = json.loads(self.body() or b"{}")
        except json.JSONDecodeError:
            raise ApiError(400, "Invalid JSON") from None
        if not isinstance(data, dict):
            raise ApiError(400, "Expected a JSON object")
        return data


class Response:
    """For non-JSON replies (file downloads, cookies)."""

    def __init__(self, body=b"", status=200, content_type="application/json", headers=None):
        self.body = body
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}


def route(method, path, public=False):
    def register(fn):
        _routes[(method, path)] = (fn, public)
        return fn

    return register


def resolve(method, raw_path):
    url = urllib.parse.urlparse(raw_path)
    entry = _routes.get((method, url.path))
    return entry, Request(None, url.path, urllib.parse.parse_qs(url.query))
