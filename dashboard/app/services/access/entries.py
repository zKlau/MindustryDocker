from ... import state


def has(entries, player_id):
    return any(entry["id"] == player_id for entry in entries)


def without(entries, player_id):
    return [entry for entry in entries if entry["id"] != player_id]


def approve(access, player_id, name):
    access["requests"] = without(access["requests"], player_id)
    if not has(access["approved"], player_id):
        access["approved"].append({"id": player_id, "name": name})


def modify(change):
    return state.modify(state.ACCESS, change)


def load():
    return state.section(state.ACCESS)
