"""Maps, campaign sectors and switching the world.

Switching uses the server's WorldReloader, the same mechanism it uses after a game over,
so connected players stay connected and are sent the new world.
"""

import re

from .. import settings
from ..server import server
from ..validation import filename, gamemode, is_msav, js_string, map_arg, map_name, sector

MAPS_JS = """(function(){
  var list = [];
  Vars.maps.all().each(function(m){
    list.push({
      name: m.plainName(), custom: m.custom, w: m.width, h: m.height, planet: m.rules().planet.name
    });
  });
  return list;
})()"""

# Named campaign sectors only; the numbered "sector-serpulo-N" ones are generic generated terrain.
SECTORS_JS = """(function(){
  var list = [];
  Vars.content.sectors().each(function(s){
    if (s.name.indexOf("sector-") == 0 || s.generator == null || s.generator.map == null) { return; }
    list.push({id: s.name, planet: s.planet.name, w: s.generator.map.width, h: s.generator.map.height});
  });
  return list;
})()"""

# Loads map `m` with gamemode MODE, keeping players connected if a game is running.
LOAD_JS = """(function(){
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


def find_js(kind, name):
    """JS statements that put the Map called `name` into variable `m` (null if not found)."""
    if kind == "sector":
        sector_id = js_string(sector(name))
        return (
            f"var s = Vars.content.sectors().find(function(s){{ return s.name == {sector_id}; }});"
            "var m = null; if (s != null) { m = s.generator.map; }"
        )
    plain_name = js_string(map_name(name))
    return f"var m = Vars.maps.all().find(function(m){{ return m.plainName() == {plain_name}; }});"


def _pretty(sector_id):
    """groundZero -> Ground Zero, caldera-erekir -> Caldera."""
    name = re.sub(r"-(erekir|serpulo)$", "", sector_id)
    name = re.sub(r"([a-z])([A-Z0-9])", r"\1 \2", name).replace("-", " ")
    return name[:1].upper() + name[1:]


def list_all():
    sectors = server.query(SECTORS_JS)
    for entry in sectors:
        entry["name"] = _pretty(entry["id"])
    return {"maps": server.query(MAPS_JS), "sectors": sectors}


def host(kind, name, mode):
    script = LOAD_JS.replace("FIND", find_js(kind, name)).replace("MODE", js_string(gamemode(mode)))
    if not server.query(script, timeout=20):
        raise ValueError("Map not found")
    server.send("say [accent]Map changed by an admin.")


def set_next(name):
    server.send(f"nextmap {map_arg(name)}")


def upload(file_name, data):
    file_name = filename(file_name, (".msav",))
    if not is_msav(data):
        raise ValueError("Not a Mindustry map file")
    settings.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    (settings.MAPS_DIR / file_name).write_bytes(data)
    server.send("reloadmaps")


def _same_name(file_stem, name):
    return file_stem.replace("_", " ").lower() == name.replace("_", " ").lower()


def delete_custom(name):
    """Delete an uploaded map file whose file name matches the map name."""
    name = map_name(name)
    for path in settings.MAPS_DIR.glob("*.msav"):
        if _same_name(path.stem, name):
            path.unlink()
            server.send("reloadmaps")
            return
    raise ValueError("Only uploaded maps whose file name matches the map name can be deleted here")
