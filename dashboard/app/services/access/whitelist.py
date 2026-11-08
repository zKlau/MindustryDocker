import time

from ...common.validation import uuid
from ...server import server
from .. import players
from . import entries
from .constants import MAX_NAME_LENGTH, MAX_REQUESTS
from .scripts import WHITELIST_ENABLED_JS


def enabled():
    return bool(server.query_or(False, WHITELIST_ENABLED_JS))


def add_request(player_id, name):
    def add(access):
        if entries.has(access["approved"], player_id):
            return
        access["requests"] = entries.without(access["requests"], player_id)
        access["requests"].insert(0, {"id": player_id, "name": name, "time": int(time.time())})
        del access["requests"][MAX_REQUESTS:]

    entries.modify(add)


def set_enabled(on):
    if not on:
        server.send("config whitelist false")

        return
    online = players.online_brief()
    for player in online:
        server.send(f"whitelist add {uuid(player['id'])}")

    def approve_online(access):
        for player in online:
            entries.approve(access, player["id"], player["name"])

    entries.modify(approve_online)
    server.send("config whitelist true")


def approve(player_id, name=""):
    player_id = uuid(player_id)
    server.send(f"whitelist add {player_id}")
    entries.modify(lambda access: entries.approve(access, player_id, str(name)[:MAX_NAME_LENGTH]))


def remove(player_id):
    player_id = uuid(player_id)
    server.send(f"whitelist remove {player_id}")
    entries.modify(lambda access: access.update(approved=entries.without(access["approved"], player_id)))


def dismiss(player_id):
    player_id = uuid(player_id)
    entries.modify(lambda access: access.update(requests=entries.without(access["requests"], player_id)))
