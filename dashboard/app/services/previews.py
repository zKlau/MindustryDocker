"""Map preview images.

The headless server never loads textures, so every block's map colour is black. On each
server start we give the blocks real colours (extracted once from Mindustry's sprites by
tools/extract_block_colors.py), then render previews with the game's own MapIO and cache
them as PNG files.
"""

import hashlib
import json
import pathlib
import threading

from .. import settings
from ..server import log, server
from ..validation import js_string
from . import maps

COLORS_FILE = pathlib.Path(__file__).resolve().parent.parent / "data" / "block_colors.json"
PREVIEW_DIR = settings.STATE_DIR / "previews"
COLORS_PER_COMMAND = 100

_render_lock = threading.Lock()
_colors_ready = threading.Event()

APPLY_COLORS_JS = """(function(){
  var colors = COLORS;
  for (var name in colors) {
    var block = Vars.content.block(name);
    if (block != null) { block.mapColor.set(Color.valueOf(colors[name])); }
  }
  return true;
})()"""

RENDER_JS = """(function(){
  FIND
  if (m == null) { return false; }
  PixmapIO.writePng(Core.files.absolute(PATH), MapIO.generatePreview(m));
  return true;
})()"""


def apply_block_colors():
    """Runs after every server start (the colours live in the server process)."""
    _colors_ready.clear()
    colors = list(json.loads(COLORS_FILE.read_text()).items())
    try:
        for start in range(0, len(colors), COLORS_PER_COMMAND):
            chunk = json.dumps(dict(colors[start : start + COLORS_PER_COMMAND]), separators=(",", ":"))
            server.query(APPLY_COLORS_JS.replace("COLORS", chunk), timeout=15)
    except RuntimeError as error:
        log(f"could not apply block colours for previews: {error}")
        return
    _colors_ready.set()


def _cache_path(kind, name):
    digest = hashlib.sha1(f"{kind}:{name}".encode()).hexdigest()[:16]
    return PREVIEW_DIR / f"{kind}-{digest}.png"


def _render(kind, name, path):
    if not _colors_ready.wait(timeout=30):
        raise RuntimeError("The server is still starting")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    script = RENDER_JS.replace("FIND", maps.find_js(kind, name)).replace("PATH", js_string(str(path)))
    if not server.query(script, timeout=30):
        raise ValueError("Map not found")


def get(kind, name):
    """PNG bytes of a map preview, rendered on first request and cached on disk."""
    path = _cache_path(kind, name)
    if not path.exists():
        with _render_lock:  # one at a time, so rendering never stalls the game for long
            if not path.exists():
                _render(kind, name, path)
    return path.read_bytes()


def forget_custom_maps():
    """Drop cached map previews after uploads or deletes (sectors never change)."""
    for path in PREVIEW_DIR.glob("map-*.png"):
        path.unlink(missing_ok=True)
