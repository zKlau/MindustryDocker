"""Player statistics and leaderboard: playtime, sessions, blocks built/broken, waves survived.

A small script installed into the server on every start counts blocks and waves per player and
reports joins. Once a minute the dashboard collects those counters and adds playtime for everyone
online, so a crash loses at most a minute. Stats are stored in /data/dashboard/stats.json.

Players can type /stats [name] and /top [category] in game.
"""

import contextlib
import json
import re
import threading
import time

from .. import settings
from ..server import log, server
from ..validation import js_string, strip_colors, uuid

STATS_FILE = settings.STATE_DIR / "stats.json"
TICK_SECONDS = 60
MAX_TICK_GAP = 2 * TICK_SECONDS  # don't count time the dashboard or server was down
TOP_COUNT = 5

CATEGORIES = {
    "playtime": "Playtime",
    "sessions": "Sessions",
    "built": "Blocks built",
    "broken": "Blocks broken",
    "waves": "Waves survived",
}

STATS_MARKER = re.compile(r"@@STATS:(join|stats|top):([^:]+):(.*)$")

INSTALL_JS = """(function(){
  if (typeof dashStats !== "undefined") { return "already installed"; }
  dashStats = {built: {}, broken: {}, waves: {}};
  var name = function(player){ return Strings.stripColors(player.name); };
  var counts = function(player){
    return typeof dashAccess === "undefined" || dashAccess.allowed(player);
  };
  var add = function(table, id){ table[id] = (table[id] || 0) + 1; };

  Events.on(EventType.PlayerJoin, function(event){
    Log.info("@@STATS:join:" + event.player.uuid() + ":" + name(event.player));
  });
  Events.on(EventType.BlockBuildEndEvent, function(event){
    if (event.unit == null) { return; }
    var player = event.unit.getPlayer();
    if (player == null || !counts(player)) { return; }
    if (event.breaking) {
      add(dashStats.broken, player.uuid());
    } else {
      add(dashStats.built, player.uuid());
    }
  });
  Events.on(EventType.WaveEvent, function(event){
    Groups.player.each(function(p){ if (counts(p)) { add(dashStats.waves, p.uuid()); } });
  });

  var register = function(text, params, description, kind){
    Vars.netServer.clientCommands.register(text, params, description, new CommandHandler.CommandRunner({
      accept: function(args, player){
        var parts = [];
        for (var i = 0; i < args.length; i++) { parts.push(String(args[i])); }
        Log.info("@@STATS:" + kind + ":" + player.uuid() + ":" + parts.join(" "));
      }
    }));
  };
  register("stats", "[player...]", "Show your stats, or another player's", "stats");
  register("top", "[playtime/built/broken/waves/sessions]", "Show the server leaderboard", "top");
  return "installed";
})()"""

# Returns and resets the counters, plus who is online (and allowed to play).
COLLECT_JS = """(function(){
  var online = [];
  Groups.player.each(function(p){
    if (typeof dashAccess === "undefined" || dashAccess.allowed(p)) {
      online.push({id: p.uuid(), name: Strings.stripColors(p.name)});
    }
  });
  var result = {online: online, built: dashStats.built, broken: dashStats.broken, waves: dashStats.waves};
  dashStats.built = {};
  dashStats.broken = {};
  dashStats.waves = {};
  return result;
})()"""

ONLINE_JS = """(function(){
  var online = [];
  Groups.player.each(function(p){ online.push(p.uuid()); });
  return online;
})()"""

MESSAGE_JS = """(function(){
  var player = Groups.player.find(function(p){ return p.uuid() == ID; });
  if (player != null) { player.sendMessage(TEXT); }
  return true;
})()"""

_lock = threading.RLock()
_last_tick = {"time": 0.0}


# ---------------------------------------------------------------- storage


def _load():
    try:
        return json.loads(STATS_FILE.read_text())
    except (OSError, ValueError):
        return {"players": {}}


def _save(data):
    settings.STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, separators=(",", ":")))
    tmp.replace(STATS_FILE)


def _player(data, player_id, name):
    now = int(time.time())
    entry = data["players"].setdefault(
        player_id,
        {"name": name, "playtime": 0, "sessions": 0, "built": 0, "broken": 0, "waves": 0, "firstSeen": now},
    )
    if name:
        entry["name"] = name
    entry["lastSeen"] = now
    return entry


# ---------------------------------------------------------------- collection


def on_server_ready():
    try:
        server.query(INSTALL_JS, timeout=15)
    except RuntimeError as error:
        log(f"could not install player stats: {error}")
    _last_tick["time"] = time.time()


def _elapsed_since_last_tick():
    now = time.time()
    elapsed = now - _last_tick["time"]
    _last_tick["time"] = now
    if elapsed > MAX_TICK_GAP:
        return 0
    return int(elapsed)


def collect():
    """Add playtime for online players and merge the block/wave counters (runs every minute)."""
    if not server.ready.is_set():
        return
    try:
        snapshot = server.query(COLLECT_JS)
    except RuntimeError:
        return
    elapsed = _elapsed_since_last_tick()
    with _lock:
        data = _load()
        for player in snapshot["online"]:
            _player(data, player["id"], player["name"])["playtime"] += elapsed
        for field in ("built", "broken", "waves"):
            for player_id, count in snapshot[field].items():
                _player(data, player_id, "")[field] += int(count)
        _save(data)


def run_collector():
    """Background loop started by __main__."""
    while True:
        time.sleep(TICK_SECONDS)
        try:
            collect()
        except Exception as error:  # noqa: BLE001 - keep counting even after an unexpected error
            log(f"stats collection failed: {error!r}")


def filter_line(line):
    """Hide stats markers and handle joins and the /stats and /top commands."""
    marker = STATS_MARKER.search(line)
    if marker is None:
        return line
    threading.Thread(target=_on_marker, args=marker.groups(), daemon=True).start()
    return None


def _on_marker(kind, player_id, argument):
    try:
        player_id = uuid(player_id)
    except ValueError:
        return  # not a real network player (e.g. a test from the console)
    if kind == "join":
        with _lock:
            data = _load()
            _player(data, player_id, argument)["sessions"] += 1
            _save(data)
    elif kind == "stats":
        _send(player_id, _stats_message(player_id, argument.strip()))
    else:
        _send(player_id, _top_message(argument.strip().lower() or "playtime"))


def _send(player_id, text):
    script = MESSAGE_JS.replace("ID", js_string(player_id)).replace("TEXT", js_string(text))
    with contextlib.suppress(RuntimeError):
        server.query(script)


# ---------------------------------------------------------------- formatting


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


def _stats_message(player_id, name):
    players = _load()["players"]
    if name:
        player_id, entry = _find_by_name(players, name)
    else:
        entry = players.get(player_id)
    if entry is None:
        return "[scarlet]No stats yet."
    rank = _rank(players, player_id)
    return (
        f"[accent]{entry['name']}[]  #{rank} by playtime\n"
        f"Playtime [accent]{format_duration(entry['playtime'])}[]  |  "
        f"Sessions [accent]{entry['sessions']}[]\n"
        f"Built [accent]{entry['built']}[]  |  Broken [accent]{entry['broken']}[]  |  "
        f"Waves [accent]{entry['waves']}[]"
    )


def _rank(players, player_id):
    order = sorted(players, key=lambda pid: players[pid]["playtime"], reverse=True)
    return order.index(player_id) + 1


def _value_text(category, value):
    if category == "playtime":
        return format_duration(value)
    return str(value)


def _top_message(category):
    if category not in CATEGORIES:
        return f"[scarlet]Unknown category. Use one of: {', '.join(CATEGORIES)}"
    players = _load()["players"].values()
    top = sorted(players, key=lambda entry: entry[category], reverse=True)[:TOP_COUNT]
    if not top:
        return "[scarlet]No stats yet."
    lines = [f"[accent]Top {len(top)} - {CATEGORIES[category]}[]"]
    for position, entry in enumerate(top, start=1):
        lines.append(f"{position}. {entry['name']}  [accent]{_value_text(category, entry[category])}[]")
    return "\n".join(lines)


# ---------------------------------------------------------------- API


def leaderboard():
    players = _load()["players"]
    online = set()
    with contextlib.suppress(RuntimeError):
        online = set(server.query(ONLINE_JS))
    entries = [
        {"id": player_id, **entry, "online": player_id in online} for player_id, entry in players.items()
    ]
    entries.sort(key=lambda entry: entry["playtime"], reverse=True)
    return {"players": entries, "categories": CATEGORIES}


def remove(player_id):
    with _lock:
        data = _load()
        data["players"].pop(str(player_id), None)
        _save(data)


def reset():
    with _lock:
        _save({"players": {}})
