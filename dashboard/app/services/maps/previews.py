import hashlib
import json
import threading

from ... import settings
from ...common.constants import KIND_MAP
from ...common.js import fill, literal
from ...common.log import log
from ...server import server
from .finder import find_js

COLORS_PER_COMMAND = 100
COMMAND_TIMEOUT = 15
RENDER_TIMEOUT = 30
COLORS_WAIT_SECONDS = 30
DIGEST_LENGTH = 16

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
    _colors_ready.clear()
    colors = list(json.loads(settings.BLOCK_COLORS_FILE.read_text()).items())
    try:
        for start in range(0, len(colors), COLORS_PER_COMMAND):
            chunk = json.dumps(dict(colors[start : start + COLORS_PER_COMMAND]), separators=(",", ":"))
            server.query(fill(APPLY_COLORS_JS, COLORS=chunk), timeout=COMMAND_TIMEOUT)
    except RuntimeError as error:
        log(f"could not apply block colours for previews: {error}")

        return
    _colors_ready.set()


def _cache_path(kind, name):
    digest = hashlib.sha1(f"{kind}:{name}".encode()).hexdigest()[:DIGEST_LENGTH]

    return settings.PREVIEW_DIR / f"{kind}-{digest}.png"


def _render(kind, name, path):
    if not _colors_ready.wait(timeout=COLORS_WAIT_SECONDS):
        raise RuntimeError("The server is still starting")
    settings.PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    script = fill(RENDER_JS, FIND=find_js(kind, name), PATH=literal(str(path)))
    if not server.query(script, timeout=RENDER_TIMEOUT):
        raise ValueError("Map not found")


def get(kind, name):
    path = _cache_path(kind, name)
    if not path.exists():
        with _render_lock:
            if not path.exists():
                _render(kind, name, path)

    return path.read_bytes()


def forget_custom_maps():
    for path in settings.PREVIEW_DIR.glob(f"{KIND_MAP}-*.png"):
        path.unlink(missing_ok=True)
