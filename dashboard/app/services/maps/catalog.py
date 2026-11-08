import re

from ...server import server

MAPS_JS = """(function(){
  var list = [];
  Vars.maps.all().each(function(m){
    list.push({
      name: m.plainName(), custom: m.custom, w: m.width, h: m.height, planet: m.rules().planet.name
    });
  });
  return list;
})()"""

NAMED_SECTORS_JS = """(function(){
  var list = [];
  Vars.content.sectors().each(function(s){
    if (s.name.indexOf("sector-") == 0 || s.generator == null || s.generator.map == null) { return; }
    list.push({id: s.name, planet: s.planet.name, w: s.generator.map.width, h: s.generator.map.height});
  });
  return list;
})()"""

PLANET_SUFFIX = re.compile(r"-(erekir|serpulo)$")
CAMEL_CASE_BOUNDARY = re.compile(r"([a-z])([A-Z0-9])")


def _pretty(sector_id):
    name = PLANET_SUFFIX.sub("", sector_id)
    name = CAMEL_CASE_BOUNDARY.sub(r"\1 \2", name).replace("-", " ")

    return name[:1].upper() + name[1:]


def list_all():
    sectors = server.query(NAMED_SECTORS_JS)
    for entry in sectors:
        entry["name"] = _pretty(entry["id"])

    return {"maps": server.query(MAPS_JS), "sectors": sectors}
