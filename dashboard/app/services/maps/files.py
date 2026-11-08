from ... import settings
from ...common.constants import MSAV_EXTENSION
from ...common.files import write_bytes
from ...common.js import fill, literal
from ...common.validation import filename, is_msav, map_name
from ...server import server
from . import previews

FIND_TIMEOUT = 10

FIND_BY_FILE_JS = """(function(){
  var m = Vars.maps.all().find(function(m){ return m.file != null && m.file.name() == FILE; });
  if (m == null) { return null; }
  return m.plainName();
})()"""


def reload():
    server.send("reloadmaps")
    previews.forget_custom_maps()


def save(path, data):
    write_bytes(path, data)
    reload()

    return server.query(fill(FIND_BY_FILE_JS, FILE=literal(path.name)), timeout=FIND_TIMEOUT)


def upload(file_name, data):
    file_name = filename(file_name, (MSAV_EXTENSION,))
    if not is_msav(data):
        raise ValueError("Not a Mindustry map file")
    write_bytes(settings.MAPS_DIR / file_name, data)
    reload()


def _same_name(file_stem, name):
    return file_stem.replace("_", " ").lower() == name.replace("_", " ").lower()


def delete_custom(name):
    name = map_name(name)
    for path in settings.MAPS_DIR.glob(f"*{MSAV_EXTENSION}"):
        if _same_name(path.stem, name):
            path.unlink()
            reload()

            return
    raise ValueError("Only uploaded maps whose file name matches the map name can be deleted here")
