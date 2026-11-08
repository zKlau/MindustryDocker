from ...common.text import strip_colors
from .constants import CATEGORIES, NO_STATS_MESSAGE, PLAYTIME, TOP_COUNT


def format_duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    minutes = rest // 60
    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def _find_by_name(players, name):
    wanted = strip_colors(name).lower()
    for player_id, entry in players.items():
        if entry["name"].lower() == wanted:
            return player_id, entry
    for player_id, entry in players.items():
        if wanted in entry["name"].lower():
            return player_id, entry

    return None, None


def _rank(players, player_id):
    order = sorted(players, key=lambda pid: players[pid][PLAYTIME], reverse=True)

    return order.index(player_id) + 1


def stats_message(players, player_id, name):
    if name:
        player_id, entry = _find_by_name(players, name)
    else:
        entry = players.get(player_id)
    if entry is None:
        return NO_STATS_MESSAGE

    return (
        f"[accent]{entry['name']}[]  #{_rank(players, player_id)} by playtime\n"
        f"Playtime [accent]{format_duration(entry[PLAYTIME])}[]  |  "
        f"Sessions [accent]{entry['sessions']}[]\n"
        f"Built [accent]{entry['built']}[]  |  Broken [accent]{entry['broken']}[]  |  "
        f"Waves [accent]{entry['waves']}[]"
    )


def _value_text(category, value):
    if category == PLAYTIME:
        return format_duration(value)

    return str(value)


def top_message(players, category):
    if category not in CATEGORIES:
        return f"[scarlet]Unknown category. Use one of: {', '.join(CATEGORIES)}"
    top = sorted(players.values(), key=lambda entry: entry[category], reverse=True)[:TOP_COUNT]
    if not top:
        return NO_STATS_MESSAGE
    lines = [f"[accent]Top {len(top)} - {CATEGORIES[category]}[]"]
    for position, entry in enumerate(top, start=1):
        lines.append(f"{position}. {entry['name']}  [accent]{_value_text(category, entry[category])}[]")

    return "\n".join(lines)
