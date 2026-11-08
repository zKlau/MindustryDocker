from ...common.threads import run_in_background
from ...common.validation import network_uuid
from .. import players
from . import messages, store
from .constants import MARKER_JOIN, MARKER_STATS, PLAYTIME, SESSIONS, STATS_MARKER


def filter_line(line):
    marker = STATS_MARKER.search(line)
    if marker is None:
        return line
    run_in_background(_on_marker, *marker.groups())

    return None


def _on_marker(kind, player_id, argument):
    player_id = network_uuid(player_id)
    if player_id is None:
        return
    argument = argument.strip()
    if kind == MARKER_JOIN:
        store.modify(lambda data: _count_session(data, player_id, argument))
    elif kind == MARKER_STATS:
        players.message(player_id, messages.stats_message(store.players(), player_id, argument))
    else:
        players.message(player_id, messages.top_message(store.players(), argument.lower() or PLAYTIME))


def _count_session(data, player_id, name):
    store.player(data, player_id, name)[SESSIONS] += 1
