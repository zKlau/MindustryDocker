from ..common.validation import non_negative_int, text
from ..server import server

CONFIG_TYPES = {
    "name": "str",
    "desc": "str",
    "motd": "str",
    "autosave": "bool",
    "autosaveAmount": "int",
    "autosaveSpacing": "int",
    "autoPause": "bool",
    "roundExtraTime": "int",
    "enableVotekick": "bool",
    "showConnectMessages": "bool",
    "antiSpam": "bool",
}
PLAYER_LIMIT = "playerLimit"
MAX_TEXT_LENGTH = 100
OFF = "off"

CONFIG_JS = """(function(){
  var values = {};
  Administration.Config.all.each(function(c){ values[c.name] = c.get(); });
  return values;
})()"""

PLAYER_LIMIT_JS = "Vars.netServer.admins.getPlayerLimit()"


def _from_server(kind, value):
    if kind == "str" and value == OFF:
        return ""

    return value


def current():
    raw = server.query(CONFIG_JS)
    values = {key: _from_server(kind, raw.get(key)) for key, kind in CONFIG_TYPES.items()}
    values[PLAYER_LIMIT] = server.query(PLAYER_LIMIT_JS)

    return {"values": values, "types": {**CONFIG_TYPES, PLAYER_LIMIT: "int"}}


def _config_value(kind, value):
    if kind == "bool":
        return str(bool(value)).lower()
    if kind == "int":
        return str(non_negative_int(value))

    return text(value, MAX_TEXT_LENGTH) or OFF


def _set_player_limit(value):
    limit = non_negative_int(value)
    if limit == 0:
        server.send(f"playerlimit {OFF}")
    else:
        server.send(f"playerlimit {limit}")


def update(values):
    for key, value in values.items():
        kind = CONFIG_TYPES.get(key)
        if kind is not None:
            server.send(f"config {key} {_config_value(kind, value)}")
    if PLAYER_LIMIT in values:
        _set_player_limit(values[PLAYER_LIMIT])
