"""Game rules: applied live and saved as the server's global rules so new maps use them too."""

import json

from .. import state
from ..server import server

# name -> type. "seconds" is shown in seconds but stored by the game in ticks (60/s).
RULES = {
    "waves": "bool",
    "waveTimer": "bool",
    "waitEnemies": "bool",
    "winWave": "int",
    "waveSpacing": "seconds",
    "infiniteResources": "bool",
    "fog": "bool",
    "coreIncinerates": "bool",
    "unitCap": "int",
    "buildSpeedMultiplier": "float",
    "buildCostMultiplier": "float",
    "unitBuildSpeedMultiplier": "float",
    "unitDamageMultiplier": "float",
    "unitHealthMultiplier": "float",
    "blockHealthMultiplier": "float",
    "blockDamageMultiplier": "float",
    "deconstructRefundMultiplier": "float",
}


def _coerce(kind, value):
    if kind == "bool":
        return bool(value)
    if kind == "int":
        return max(0, int(float(value)))
    return max(0.0, float(value))


READ_JS = """(function(){
  var rules = Vars.state.rules;
  var values = {};
  KEYS.forEach(function(key){ values[key] = rules[key]; });
  return values;
})()"""

APPLY_JS = "(function(){ var r = Vars.state.rules; ASSIGNMENTS Call.setRules(r); return true; })()"


def current():
    live = server.query(READ_JS.replace("KEYS", json.dumps(list(RULES))))
    live["waveSpacing"] = round(live.get("waveSpacing", 0) / 60)
    return {"live": live, "overrides": state.load()["rules"], "types": RULES}


def apply(values):
    overrides = state.load()["rules"]
    assignments = []
    for key, raw in values.items():
        kind = RULES.get(key)
        if kind is None:
            continue
        value = _coerce(kind, raw)
        overrides[key] = value
        if kind == "seconds":
            value_in_game = value * 60  # the game stores this in ticks
        else:
            value_in_game = value
        game_value = json.dumps(value_in_game)
        server.send(f"rules add {key} {game_value}")
        assignments.append(f"r.{key}={game_value};")
    state.update("rules", overrides)
    if assignments and server.hosting():
        server.query(APPLY_JS.replace("ASSIGNMENTS", " ".join(assignments)))


def reset():
    for key in RULES:
        server.send(f"rules remove {key}")
    state.update("rules", {})
