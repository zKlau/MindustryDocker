"""Server settings (the `config` console command) and player limit."""

from ..server import server

# name -> type
CONFIGS = {
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

CONFIG_JS = """(function(){
  var values = {};
  Administration.Config.all.each(function(c){ values[c.name] = c.get(); });
  return values;
})()"""


def current():
    raw = server.query(CONFIG_JS)
    values = {}
    for key, kind in CONFIGS.items():
        value = raw.get(key)
        if kind == "str" and value == "off":
            value = ""  # the server uses "off" for empty text settings
        values[key] = value
    values["playerLimit"] = server.query("Vars.netServer.admins.getPlayerLimit()")
    return {"values": values, "types": {**CONFIGS, "playerLimit": "int"}}


def _config_value(kind, value):
    if kind == "bool":
        return str(bool(value)).lower()
    if kind == "int":
        return str(max(0, int(float(value))))
    text = str(value).strip()[:100]
    if not text:
        return "off"
    return text


def _set_player_limit(value):
    limit = max(0, int(float(value or 0)))
    if limit == 0:
        server.send("playerlimit off")
    else:
        server.send(f"playerlimit {limit}")


def update(values):
    for key, value in values.items():
        kind = CONFIGS.get(key)
        if kind is not None:
            server.send(f"config {key} {_config_value(kind, value)}")
    if "playerLimit" in values:
        _set_player_limit(values["playerLimit"])
