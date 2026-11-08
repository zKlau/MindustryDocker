from ...common.js import fill, literal
from ...common.validation import gamemode, map_arg
from ...server import server
from .finder import find_js

HOST_TIMEOUT = 20

LOAD_KEEPING_PLAYERS_CONNECTED_JS = """(function(){
  FIND
  if (m == null) { return false; }
  var mode = Gamemode.valueOf(MODE);
  if (Vars.state.isMenu()) {
    Vars.logic.reset();
    Vars.world.loadMap(m, m.applyRules(mode));
    Vars.state.rules = m.applyRules(mode);
    Vars.logic.play();
    Vars.netServer.openServer();
  } else {
    var reloader = new WorldReloader();
    reloader.begin();
    Vars.world.loadMap(m, m.applyRules(mode));
    Vars.state.rules = m.applyRules(mode);
    Vars.logic.play();
    reloader.end();
  }
  return true;
})()"""


def host(kind, name, mode):
    script = fill(LOAD_KEEPING_PLAYERS_CONNECTED_JS, FIND=find_js(kind, name), MODE=literal(gamemode(mode)))
    if not server.query(script, timeout=HOST_TIMEOUT):
        raise ValueError("Map not found")
    server.send("say [accent]Map changed by an admin.")


def set_next(name):
    server.send(f"nextmap {map_arg(name)}")
