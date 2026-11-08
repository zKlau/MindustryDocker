import threading
import time

from ... import settings
from ...common.files import read_json, write_json_atomic
from .constants import CATEGORIES

_lock = threading.RLock()


def _empty():
    return {"players": {}}


def players():
    return read_json(settings.STATS_FILE, _empty())["players"]


def modify(change):
    with _lock:
        data = read_json(settings.STATS_FILE, _empty())
        change(data)
        write_json_atomic(settings.STATS_FILE, data)


def reset():
    modify(lambda data: data.update(_empty()))


def player(data, player_id, name):
    now = int(time.time())
    entry = data["players"].setdefault(
        player_id, {"name": name, **dict.fromkeys(CATEGORIES, 0), "firstSeen": now}
    )
    if name:
        entry["name"] = name
    entry["lastSeen"] = now

    return entry
