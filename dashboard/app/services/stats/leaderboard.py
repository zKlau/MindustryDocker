from .. import players
from . import store
from .constants import CATEGORIES, PLAYTIME


def leaderboard():
    online = {player["id"] for player in players.online_brief()}
    entries = [
        {"id": player_id, **entry, "online": player_id in online}
        for player_id, entry in store.players().items()
    ]
    entries.sort(key=lambda entry: entry[PLAYTIME], reverse=True)

    return {"players": entries, "categories": CATEGORIES}


def remove(player_id):
    store.modify(lambda data: data["players"].pop(str(player_id), None))


def reset():
    store.reset()
