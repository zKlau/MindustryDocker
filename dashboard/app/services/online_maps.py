"""Browse and install maps from MindustryTool (mindustry-tool.com).

Uses the same public API as the MindustryTool game mod. It is undocumented, so errors are
reported to the dashboard instead of breaking anything else.
"""

import re

from .. import http_client, settings
from ..server import server
from ..validation import is_msav, item_id, js_string, strip_colors
from . import maps, previews

API = "https://api.mindustry-tool.com/api/v4"
PAGE_SIZE = 24
SORTS = {"popular": "download-count_desc", "liked": "like_desc", "newest": "time_desc"}
PREVIEW_DIR = settings.STATE_DIR / "online-previews"
MAP_LIMIT = 50 * 1024 * 1024
PREVIEW_LIMIT = 8 * 1024 * 1024

PLANET_RULE = re.compile(r"planet\W+(\w+)")

FIND_BY_FILE_JS = """(function(){
  var m = Vars.maps.all().find(function(m){ return m.file != null && m.file.name() == FILE; });
  if (m == null) { return null; }
  return m.plainName();
})()"""


def search(query="", sort="popular", page=0):
    params = {
        "page": max(0, int(page)),
        "size": PAGE_SIZE,
        "sort": SORTS.get(sort, SORTS["popular"]),
    }
    query = str(query).strip()[:60]
    if query:
        params["name"] = query
    url = f"{API}/maps?{http_client.urlencode(params)}"
    items = http_client.fetch_json(url)
    results = [
        {
            "id": item["itemId"],
            "name": strip_colors(item["name"]),
            "likes": item["likes"],
            "downloads": item["downloads"],
        }
        for item in items
    ]
    return {"maps": results, "hasMore": len(items) == PAGE_SIZE}


def _planet(meta):
    match = PLANET_RULE.search(str(meta.get("rules", "")))
    if match is None:
        return ""
    return match.group(1)


def details(map_id):
    data = http_client.fetch_json(f"{API}/maps/{item_id(map_id)}")
    meta = data.get("meta") or {}
    return {
        "id": data["itemId"],
        "name": strip_colors(data.get("name")),
        "description": strip_colors(data.get("description")),
        "author": strip_colors(meta.get("author")),
        "width": data.get("width"),
        "height": data.get("height"),
        "planet": _planet(meta),
        "tags": data.get("tags") or [],
        "likes": data.get("likes", 0),
        "downloads": data.get("downloads", 0),
    }


def preview(map_id):
    """Preview PNG, fetched once and cached on disk."""
    map_id = item_id(map_id)
    path = PREVIEW_DIR / f"{map_id}.png"
    if not path.exists():
        image = http_client.fetch(f"{API}/maps/{map_id}/image.png?variant=preview", limit=PREVIEW_LIMIT)
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image)
    return path.read_bytes()


def _file_name(name, map_id):
    """Readable and stable: reinstalling the same map overwrites its file instead of adding a copy."""
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")[:50] or "map"
    return settings.MAPS_DIR / f"{slug}-{map_id[:8]}.msav"


def install(map_id):
    """Download the map into the server's maps folder. Returns its in-game name."""
    info = details(map_id)
    data = http_client.fetch(f"{API}/maps/{info['id']}/data", limit=MAP_LIMIT, timeout=60)
    if not is_msav(data):
        raise ValueError("MindustryTool returned something that is not a map file")
    settings.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    path = _file_name(info["name"], info["id"])
    path.write_bytes(data)
    server.send("reloadmaps")
    previews.forget_custom_maps()
    in_game_name = server.query(FIND_BY_FILE_JS.replace("FILE", js_string(path.name)), timeout=10)
    if not in_game_name:
        raise ValueError("The map was downloaded but the server could not load it (it may need a mod)")
    return in_game_name


def install_and_play(map_id, mode):
    name = install(map_id)
    maps.host("map", name, mode)
    return name
