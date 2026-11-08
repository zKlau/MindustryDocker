from ... import settings
from ...common.constants import MOD_EXTENSIONS
from ...common.files import write_bytes
from ...common.text import first_line, strip_colors
from ...common.validation import filename, is_zip
from ...server import server

LOADED_JS = """(function(){
  var list = [];
  Vars.mods.list().each(function(m){
    try {
      list.push({
        name: String(m.meta.displayName || m.name),
        version: String(m.meta.version || ""),
        file: String(m.file.name()),
        error: m.hasContentErrors() || !m.isSupported()
      });
    } catch (e) {
      list.push({name: String(m.name), version: "", file: String(m.file.name()), error: true});
    }
  });
  return list;
})()"""


def files():
    if not settings.MODS_DIR.exists():
        return []

    return sorted(
        path
        for path in settings.MODS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in MOD_EXTENSIONS
    )


def _loaded_mods():
    if not server.alive():
        return {}

    return {mod["file"]: mod for mod in server.query(LOADED_JS)}


def _describe(path, loaded):
    info = loaded.get(path.name)
    entry = {
        "file": path.name,
        "size": path.stat().st_size,
        "name": path.stem,
        "version": "",
        "error": False,
        "loaded": info is not None,
    }
    if info is not None:
        entry.update(
            name=strip_colors(info["name"]) or path.stem,
            version=first_line(info["version"]),
            error=info["error"],
        )

    return entry


def list_all():
    loaded = _loaded_mods()

    return [_describe(path, loaded) for path in files()]


def save(stem, extension, data):
    for old in settings.MODS_DIR.glob(f"{stem}.*"):
        old.unlink()
    target = settings.MODS_DIR / f"{stem}{extension}"
    write_bytes(target, data)

    return target.name


def upload(file_name, data):
    file_name = filename(file_name, MOD_EXTENSIONS)
    if not is_zip(data):
        raise ValueError("Mods must be .jar or .zip files")
    write_bytes(settings.MODS_DIR / file_name, data)


def delete(file_name):
    (settings.MODS_DIR / filename(file_name, MOD_EXTENSIONS)).unlink(missing_ok=True)
