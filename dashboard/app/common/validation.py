import re
import zlib

from .constants import DEFAULT_GAMEMODE, GAMEMODES

_SLOT = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_PRINTABLE_MAP_NAME = re.compile(r"^[^\x00-\x1f\x7f]{1,100}$")
_UUID = re.compile(r"^[A-Za-z0-9+/=]{4,64}$")
_SECTOR = re.compile(r"^[A-Za-z0-9\-]{1,64}$")
_FILE = re.compile(r"^[A-Za-z0-9_\-. ]{1,100}$")
_ITEM_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_REPO = re.compile(r"^[A-Za-z0-9_.\-]{1,100}/[A-Za-z0-9_.\-]{1,100}$")

_ZIP_MAGIC = b"PK"
_MSAV_MAGIC = b"MSAV"
_MSAV_PROBE_BYTES = 4096


def _matching(value, pattern, message):
    value = str(value).strip()
    if not pattern.match(value):
        raise ValueError(message)

    return value


def slot(name):
    return _matching(name, _SLOT, "Use letters, numbers, - and _ only")


def map_name(name):
    return _matching(name, _PRINTABLE_MAP_NAME, "Invalid map name")


def map_arg(name):
    return map_name(name).replace(" ", "_")


def sector(name):
    return _matching(name, _SECTOR, "Invalid sector")


def uuid(value):
    return _matching(value, _UUID, "Invalid player ID")


def network_uuid(value):
    try:
        return uuid(value)
    except ValueError:
        return None


def gamemode(value):
    value = str(value or DEFAULT_GAMEMODE)
    if value not in GAMEMODES:
        raise ValueError("Invalid game mode")

    return value


def filename(value, extensions):
    value = str(value).strip().replace("\\", "/").split("/")[-1]
    if not _FILE.match(value) or value.startswith(".") or not value.lower().endswith(extensions):
        raise ValueError(f"File must be {' or '.join(extensions)}")

    return value


def item_id(value):
    return _matching(str(value).lower(), _ITEM_ID, "Invalid map id")


def repo(value):
    return _matching(value, _REPO, "Invalid repository")


def text(value, max_length):
    return str(value).strip()[:max_length]


def non_negative_int(value):
    return max(0, int(float(value or 0)))


def non_negative_float(value):
    return max(0.0, float(value or 0))


def is_msav(data):
    try:
        return zlib.decompressobj().decompress(data[:_MSAV_PROBE_BYTES]).startswith(_MSAV_MAGIC)
    except zlib.error:
        return False


def is_zip(data):
    return data.startswith(_ZIP_MAGIC)
