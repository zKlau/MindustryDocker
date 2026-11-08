import time

from ...common.log import log
from ...server import server
from . import store
from .constants import INSTALL_TIMEOUT, MAX_COUNTED_GAP_SECONDS, PLAYTIME, SCRIPT_COUNTERS, TICK_SECONDS
from .scripts import COLLECT_AND_RESET_COUNTERS_JS, INSTALL_JS

_last_tick = {"time": 0.0}


def on_server_ready():
    try:
        server.query(INSTALL_JS, timeout=INSTALL_TIMEOUT)
    except RuntimeError as error:
        log(f"could not install player stats: {error}")
    _last_tick["time"] = time.time()


def _elapsed_since_last_tick():
    now = time.time()
    elapsed = now - _last_tick["time"]
    _last_tick["time"] = now
    if elapsed > MAX_COUNTED_GAP_SECONDS:
        return 0

    return int(elapsed)


def collect():
    if not server.ready.is_set():
        return
    try:
        snapshot = server.query(COLLECT_AND_RESET_COUNTERS_JS)
    except RuntimeError:
        return
    elapsed = _elapsed_since_last_tick()

    def merge(data):
        for player in snapshot["online"]:
            store.player(data, player["id"], player["name"])[PLAYTIME] += elapsed
        for field in SCRIPT_COUNTERS:
            for player_id, count in snapshot[field].items():
                store.player(data, player_id, "")[field] += int(count)

    store.modify(merge)


def run_collector():
    while True:
        time.sleep(TICK_SECONDS)
        try:
            collect()
        except Exception as error:
            log(f"stats collection failed: {error!r}")
