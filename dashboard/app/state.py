import copy
import threading

from . import settings
from .common.constants import DEFAULT_GAMEMODE, KIND_MAP
from .common.files import read_json, write_json_atomic

RULES = "rules"
STARTUP = "startup"
ACCESS = "access"

_lock = threading.RLock()

DEFAULTS = {
    RULES: {},
    STARTUP: {"mode": "resume", "kind": KIND_MAP, "map": "", "gamemode": DEFAULT_GAMEMODE},
    ACCESS: {
        "passwordEnabled": False,
        "password": "",
        "remembered": [],
        "approved": [],
        "requests": [],
    },
}


def load():
    with _lock:
        data = read_json(settings.STATE_FILE, {})
    merged = copy.deepcopy(DEFAULTS)
    for key, value in data.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value

    return merged


def section(key):
    return load()[key]


def update(key, value):
    with _lock:
        data = load()
        data[key] = value
        write_json_atomic(settings.STATE_FILE, data, indent=2, private=True)

    return data


def modify(key, change):
    with _lock:
        current = section(key)
        change(current)
        update(key, current)

        return current
