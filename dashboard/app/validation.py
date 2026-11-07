"""Input validation shared by the services. Everything that ends up in a console command goes through here."""

import json
import re
import zlib

_SLOT = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
# Map names can contain any printable characters; they only reach the console quoted (JS) or as a
# single line (newlines are stripped by server.send), so only control characters are rejected.
_MAP = re.compile(r"^[^\x00-\x1f\x7f]{1,100}$")
_UUID = re.compile(r"^[A-Za-z0-9+/=]{4,64}$")
_SECTOR = re.compile(r"^[A-Za-z0-9\-]{1,64}$")
_FILE = re.compile(r"^[A-Za-z0-9_\-. ]{1,100}$")
_ITEM_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_COLOR_TAG = re.compile(r"\[[^\[\]]*\]")
_REPO = re.compile(r"^[A-Za-z0-9_.\-]{1,100}/[A-Za-z0-9_.\-]{1,100}$")

GAMEMODES = ("survival", "sandbox", "attack", "pvp")


def slot(name):
    name = str(name).strip()
    if not _SLOT.match(name):
        raise ValueError("Use letters, numbers, - and _ only")
    return name


def map_name(name):
    name = str(name).strip()
    if not _MAP.match(name):
        raise ValueError("Invalid map name")
    return name


def map_arg(name):
    """Map names are passed to `host` with spaces as underscores (the server converts them back)."""
    return map_name(name).replace(" ", "_")


def sector(name):
    name = str(name).strip()
    if not _SECTOR.match(name):
        raise ValueError("Invalid sector")
    return name


def uuid(value):
    value = str(value).strip()
    if not _UUID.match(value):
        raise ValueError("Invalid player ID")
    return value


def gamemode(value):
    value = str(value or "survival")
    if value not in GAMEMODES:
        raise ValueError("Invalid game mode")
    return value


def filename(value, extensions):
    value = str(value).strip().replace("\\", "/").split("/")[-1]
    if not _FILE.match(value) or value.startswith(".") or not value.lower().endswith(extensions):
        raise ValueError(f"File must be {' or '.join(extensions)}")
    return value


def js_string(value):
    return json.dumps(str(value))


def item_id(value):
    """A MindustryTool item id (UUID)."""
    value = str(value).strip().lower()
    if not _ITEM_ID.match(value):
        raise ValueError("Invalid map id")
    return value


def repo(value):
    """A GitHub repository in owner/name form."""
    value = str(value).strip()
    if not _REPO.match(value):
        raise ValueError("Invalid repository")
    return value


def is_msav(data):
    """Mindustry maps and saves are zlib-compressed and start with "MSAV" once decompressed."""
    try:
        return zlib.decompressobj().decompress(data[:4096]).startswith(b"MSAV")
    except zlib.error:
        return False


def strip_colors(text):
    """Remove Mindustry colour tags like [gold] from names and descriptions."""
    return _COLOR_TAG.sub("", str(text or "")).strip()
