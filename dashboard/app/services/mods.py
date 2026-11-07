"""Mods and plugins (files in config/mods). Changes take effect after a server restart."""

from .. import settings
from ..server import server
from ..validation import filename, strip_colors

EXTENSIONS = (".jar", ".zip")

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


def _loaded_mods():
    if not server.alive():
        return {}
    return {mod["file"]: mod for mod in server.query(LOADED_JS)}


def _describe(path, loaded):
    info = loaded.get(path.name)
    entry = {"file": path.name, "size": path.stat().st_size, "name": path.stem, "version": "", "error": False}
    entry["loaded"] = info is not None
    if info is not None:
        version_lines = strip_colors(info["version"]).splitlines() or [""]
        entry.update(
            name=strip_colors(info["name"]) or path.stem, version=version_lines[0], error=info["error"]
        )
    return entry


def list_all():
    if not settings.MODS_DIR.exists():
        return []
    loaded = _loaded_mods()
    files = sorted(p for p in settings.MODS_DIR.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
    return [_describe(path, loaded) for path in files]


def upload(file_name, data):
    file_name = filename(file_name, EXTENSIONS)
    if not data.startswith(b"PK"):
        raise ValueError("Mods must be .jar or .zip files")
    settings.MODS_DIR.mkdir(parents=True, exist_ok=True)
    (settings.MODS_DIR / file_name).write_bytes(data)


def delete(file_name):
    (settings.MODS_DIR / filename(file_name, EXTENSIONS)).unlink(missing_ok=True)
