from ...common.constants import KIND_SECTOR
from ...common.js import fill, literal
from ...common.validation import map_name, sector

FIND_SECTOR_JS = (
    "var s = Vars.content.sectors().find(function(s){ return s.name == NAME; });"
    "var m = null; if (s != null) { m = s.generator.map; }"
)
FIND_MAP_JS = "var m = Vars.maps.all().find(function(m){ return m.plainName() == NAME; });"


def find_js(kind, name):
    if kind == KIND_SECTOR:
        return fill(FIND_SECTOR_JS, NAME=literal(sector(name)))

    return fill(FIND_MAP_JS, NAME=literal(map_name(name)))
