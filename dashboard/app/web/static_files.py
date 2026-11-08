import mimetypes
import urllib.parse

from .. import settings
from .constants import BINARY_TYPE, INDEX_FILE, STATIC_CACHE

STATIC_ROOT = settings.STATIC_DIR.resolve()

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")


def _resolve(path):
    rel = urllib.parse.unquote(path).lstrip("/") or INDEX_FILE
    target = (STATIC_ROOT / rel).resolve()
    if STATIC_ROOT not in target.parents or not target.is_file():
        return STATIC_ROOT / INDEX_FILE

    return target


def _content_type(target):
    content_type = mimetypes.guess_type(target.name)[0] or BINARY_TYPE
    if content_type.startswith("text/"):
        content_type += "; charset=utf-8"

    return content_type


def load(path):
    target = _resolve(path)
    headers = {}
    if target.name != INDEX_FILE:
        headers["Cache-Control"] = STATIC_CACHE

    return target.read_bytes(), _content_type(target), headers
