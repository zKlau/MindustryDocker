"""Join protection: a chat login password and/or Mindustry's built-in whitelist.

Join password
  Players type `/login <password>` in chat. Until they do, they can't build, chat or interact,
  and they are kicked after LOGIN_TIMEOUT seconds. Players who logged in once are remembered
  by their player ID. Admins never need to log in. The check runs inside the server through a
  small script installed on every server start; the password never appears in any log.

Whitelist
  Mindustry's own whitelist: only approved player IDs can join. When someone who isn't on
  the list tries to join, the server logs their ID; the dashboard turns that into a request
  you can approve.
"""

import contextlib
import json
import re
import threading
import time

from .. import state
from ..server import log, server
from ..validation import js_string, uuid

LOGIN_TIMEOUT = 60
MAX_REQUESTS = 50
MAX_PASSWORD_LENGTH = 64

ACCESS_MARKER = re.compile(r"@@ACCESS:(login|failed):([^:]+):(.*)$")
WHITELIST_REQUEST = re.compile(r"whitelist add (\S+) to whitelist the player '(.*)'")
LOGIN_COMMAND = re.compile(r"(/login)\s+\S.*", re.IGNORECASE)

# Installed once per server process; the global `dashAccess` keeps its state.
INSTALL_JS = """(function(){
  if (typeof dashAccess !== "undefined") { return "already installed"; }
  dashAccess = {enabled: false, password: "", remembered: {}, timeout: TIMEOUT};

  dashAccess.allowed = function(player){
    if (!dashAccess.enabled || player == null || player.admin) { return true; }
    return dashAccess.remembered[player.uuid()] === true;
  };

  var name = function(player){ return Strings.stripColors(player.name); };

  var login = function(args, player){
    if (!dashAccess.enabled) { player.sendMessage("[accent]This server has no password."); return; }
    if (dashAccess.allowed(player)) { player.sendMessage("[accent]You are already logged in."); return; }
    if (args[0] == dashAccess.password) {
      dashAccess.remembered[player.uuid()] = true;
      Log.info("@@ACCESS:login:" + player.uuid() + ":" + name(player));
      player.sendMessage("[green]Logged in. Have fun!");
    } else {
      Log.info("@@ACCESS:failed:" + player.uuid() + ":" + name(player));
      player.sendMessage("[scarlet]Wrong password.");
    }
  };
  Vars.netServer.clientCommands.register("login", "<password>", "Log in with the server password",
    new CommandHandler.CommandRunner({accept: login}));

  Vars.netServer.admins.addChatFilter(function(player, text){
    if (dashAccess.allowed(player)) { return text; }
    player.sendMessage("[scarlet]Log in first: [white]/login <password>");
    return null;
  });
  Vars.netServer.admins.addActionFilter(function(action){ return dashAccess.allowed(action.player); });

  var kickIfStillLoggedOut = function(id){
    Core.app.post(function(){
      var player = Groups.player.find(function(p){ return p.uuid() == id; });
      if (player != null && !dashAccess.allowed(player)) {
        player.kick("Login timed out. Get the password from the host, then type /login <password>.", 0);
      }
    });
  };

  Events.on(EventType.PlayerJoin, function(event){
    var player = event.player;
    if (dashAccess.allowed(player)) { return; }
    var seconds = dashAccess.timeout;
    var text = "This server needs a password.\\n\\nType [accent]/login <password>[] in chat within ";
    Call.infoMessage(player.con, text + seconds + " seconds.");
    player.sendMessage("[accent]Type /login <password> to play.");
    var id = player.uuid();
    Timer.schedule(function(){ kickIfStillLoggedOut(id); }, seconds);
  });
  return "installed";
})()"""

CONFIGURE_JS = """(function(){
  dashAccess.enabled = ENABLED;
  dashAccess.password = PASSWORD;
  dashAccess.remembered = REMEMBERED;
  return true;
})()"""

ONLINE_JS = """(function(){
  var list = [];
  Groups.player.each(function(p){ list.push({id: p.uuid(), name: Strings.stripColors(p.name)}); });
  return list;
})()"""

WHITELIST_ENABLED_JS = "Administration.Config.whitelist.bool()"


# ---------------------------------------------------------------- server hooks


def on_server_ready():
    """Install the login script and push the current settings (runs after every server start)."""
    try:
        server.query(INSTALL_JS.replace("TIMEOUT", str(LOGIN_TIMEOUT)), timeout=15)
        _push_password_settings()
    except RuntimeError as error:
        log(f"could not install join protection: {error}")


def filter_line(line):
    """Hide login markers, record whitelist requests and blank out typed passwords."""
    marker = ACCESS_MARKER.search(line)
    if marker:
        threading.Thread(target=_on_login_event, args=marker.groups(), daemon=True).start()
        return None
    request = WHITELIST_REQUEST.search(line)
    if request:
        threading.Thread(target=_add_request, args=request.groups(), daemon=True).start()
    return LOGIN_COMMAND.sub(r"\1 ****", line)


def _on_login_event(kind, player_id, name):
    try:
        player_id = uuid(player_id)
    except ValueError:
        return  # not a real network player (e.g. a test from the console)
    if kind == "failed":
        log(f"wrong join password from {name}")
        return
    log(f"{name} logged in with the join password")

    def remember(access):
        if player_id not in access["remembered"]:
            access["remembered"].append(player_id)

    state.modify("access", remember)


def _add_request(player_id, name):
    def add(access):
        if any(entry["id"] == player_id for entry in access["approved"]):
            return
        access["requests"] = [entry for entry in access["requests"] if entry["id"] != player_id]
        access["requests"].insert(0, {"id": player_id, "name": name, "time": int(time.time())})
        del access["requests"][MAX_REQUESTS:]

    state.modify("access", add)


def _push_password_settings():
    access = state.load()["access"]
    remembered = {player_id: True for player_id in access["remembered"]}
    script = (
        CONFIGURE_JS.replace("ENABLED", json.dumps(bool(access["passwordEnabled"])))
        .replace("PASSWORD", js_string(access["password"]))
        .replace("REMEMBERED", json.dumps(remembered))
    )
    server.query(script)


def _online_players():
    try:
        return server.query(ONLINE_JS)
    except RuntimeError:
        return []


# ---------------------------------------------------------------- API


def status():
    access = state.load()["access"]
    whitelist_enabled = False
    with contextlib.suppress(RuntimeError):
        whitelist_enabled = bool(server.query(WHITELIST_ENABLED_JS))
    return {
        "passwordEnabled": access["passwordEnabled"],
        "hasPassword": bool(access["password"]),
        "rememberedCount": len(access["remembered"]),
        "loginTimeout": LOGIN_TIMEOUT,
        "whitelistEnabled": whitelist_enabled,
        "approved": access["approved"],
        "requests": access["requests"],
    }


def _validate_password(password):
    password = str(password)
    if len(password) > MAX_PASSWORD_LENGTH or any(c.isspace() for c in password):
        raise ValueError(f"Use up to {MAX_PASSWORD_LENGTH} characters without spaces")
    return password


def set_password(enabled, password=None):
    """Turn the join password on/off and optionally change it.

    Changing the password forgets everyone who logged in before. Players online when the
    password is turned on are remembered, so nobody gets kicked mid-game.
    """
    online_ids = [player["id"] for player in _online_players()]

    def change(access):
        if password:
            access["password"] = _validate_password(password)
            access["remembered"] = []
        if enabled and not access["password"]:
            raise ValueError("Set a password first")
        if enabled and not access["passwordEnabled"]:
            access["remembered"] = sorted(set(access["remembered"]) | set(online_ids))
        access["passwordEnabled"] = bool(enabled)

    state.modify("access", change)
    if enabled:
        # Keep "/login <password>" out of Mindustry's own log files. The container log (shown in
        # the dashboard) stays on and has the password blanked out by filter_line().
        server.send("config logCommands false")
        server.send("config logging false")
    _push_password_settings()


def forget_logins():
    state.modify("access", lambda access: access.update(remembered=[]))
    _push_password_settings()


def _approve(access, player_id, name):
    access["requests"] = [entry for entry in access["requests"] if entry["id"] != player_id]
    if not any(entry["id"] == player_id for entry in access["approved"]):
        access["approved"].append({"id": player_id, "name": name})


def set_whitelist(enabled):
    """Turn the whitelist on/off. Turning it on approves everyone online, so nobody is locked out."""
    if enabled:
        online = _online_players()
        for player in online:
            server.send(f"whitelist add {uuid(player['id'])}")

        def approve_online(access):
            for player in online:
                _approve(access, player["id"], player["name"])

        state.modify("access", approve_online)
        server.send("config whitelist true")
    else:
        server.send("config whitelist false")


def approve(player_id, name=""):
    player_id = uuid(player_id)
    server.send(f"whitelist add {player_id}")
    state.modify("access", lambda access: _approve(access, player_id, str(name)[:60]))


def remove(player_id):
    player_id = uuid(player_id)
    server.send(f"whitelist remove {player_id}")

    def drop(access):
        access["approved"] = [entry for entry in access["approved"] if entry["id"] != player_id]

    state.modify("access", drop)


def dismiss(player_id):
    player_id = uuid(player_id)

    def drop(access):
        access["requests"] = [entry for entry in access["requests"] if entry["id"] != player_id]

    state.modify("access", drop)
