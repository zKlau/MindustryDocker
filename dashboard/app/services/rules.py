from .. import state
from ..common.constants import TICKS_PER_SECOND
from ..common.js import fill, literal
from ..common.validation import non_negative_float, non_negative_int
from ..server import server

RULE_TYPES = {
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

READ_JS = """(function(){
  var rules = Vars.state.rules;
  var values = {};
  KEYS.forEach(function(key){ values[key] = rules[key]; });
  return values;
})()"""

APPLY_JS = "(function(){ var r = Vars.state.rules; ASSIGNMENTS Call.setRules(r); return true; })()"


def _coerce(kind, value):
    if kind == "bool":
        return bool(value)
    if kind == "int":
        return non_negative_int(value)

    return non_negative_float(value)


def _to_game(kind, value):
    if kind == "seconds":
        return value * TICKS_PER_SECOND

    return value


def current():
    live = server.query(fill(READ_JS, KEYS=literal(list(RULE_TYPES))))
    live["waveSpacing"] = round(live.get("waveSpacing", 0) / TICKS_PER_SECOND)

    return {"live": live, "overrides": state.section(state.RULES), "types": RULE_TYPES}


def apply(values):
    overrides = state.section(state.RULES)
    assignments = []
    for key, raw in values.items():
        kind = RULE_TYPES.get(key)
        if kind is None:
            continue
        value = _coerce(kind, raw)
        overrides[key] = value
        game_value = literal(_to_game(kind, value))
        server.send(f"rules add {key} {game_value}")
        assignments.append(f"r.{key}={game_value};")
    state.update(state.RULES, overrides)
    if assignments and server.hosting():
        server.query(fill(APPLY_JS, ASSIGNMENTS=" ".join(assignments)))


def reset():
    for key in RULE_TYPES:
        server.send(f"rules remove {key}")
    state.update(state.RULES, {})
