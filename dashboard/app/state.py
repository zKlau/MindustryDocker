"""Small JSON store for dashboard-owned settings (rule overrides, startup behaviour)."""

import copy
import json
import threading

from . import settings

_lock = threading.Lock()

DEFAULTS = {
    "rules": {},
    # What to do when the server process starts:
    #   resume  - load the save made at the last shutdown (falls back to MINDUSTRY_START_COMMANDS)
    #   map     - host a specific map/sector with a mode
    #   env     - just run MINDUSTRY_START_COMMANDS
    "startup": {"mode": "resume", "kind": "map", "map": "", "gamemode": "survival"},
}


def load():
    with _lock:
        try:
            data = json.loads(settings.STATE_FILE.read_text())
        except (OSError, ValueError):
            data = {}
    merged = copy.deepcopy(DEFAULTS)
    for key, value in data.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def update(key, value):
    data = load()
    data[key] = value
    with _lock:
        settings.STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = settings.STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(settings.STATE_FILE)
    return data
