import re

from ... import settings
from ...common import http_client
from ...common.constants import KIND_MAP, MAX_SEARCH_QUERY_LENGTH, MB, MSAV_EXTENSION
from ...common.files import write_bytes
from ...common.text import slugify, strip_colors
from ...common.validation import is_msav, item_id, text
from . import files, hosting

API = "https://api.mindustry-tool.com/api/v4"
PAGE_SIZE = 24
DEFAULT_SORT = "popular"
SORTS = {DEFAULT_SORT: "download-count_desc", "liked": "like_desc", "newest": "time_desc"}
MAP_LIMIT = 50 * MB
PREVIEW_LIMIT = 8 * MB
DOWNLOAD_TIMEOUT = 60
SLUG_LENGTH = 50
ID_PREFIX_LENGTH = 8

PLANET_RULE = re.compile(r"planet\W+(\w+)")


def _summary(item):
    return {
        "id": item["itemId"],
        "name": strip_colors(item["name"]),
        "likes": item["likes"],
        "downloads": item["downloads"],
    }


def search(query="", sort=DEFAULT_SORT, page=0):
    params = {
        "page": max(0, int(page)),
        "size": PAGE_SIZE,
        "sort": SORTS.get(sort, SORTS[DEFAULT_SORT]),
    }
    query = text(query, MAX_SEARCH_QUERY_LENGTH)
    if query:
        params["name"] = query
    items = http_client.fetch_json(f"{API}/maps?{http_client.urlencode(params)}")

    return {"maps": [_summary(item) for item in items], "hasMore": len(items) == PAGE_SIZE}


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
    map_id = item_id(map_id)
    path = settings.ONLINE_PREVIEW_DIR / f"{map_id}.png"
    if not path.exists():
        image = http_client.fetch(f"{API}/maps/{map_id}/image.png?variant=preview", limit=PREVIEW_LIMIT)
        write_bytes(path, image)

    return path.read_bytes()


def _file_path(name, map_id):
    slug = slugify(name, "_", SLUG_LENGTH, KIND_MAP)

    return settings.MAPS_DIR / f"{slug}-{map_id[:ID_PREFIX_LENGTH]}{MSAV_EXTENSION}"


def install(map_id):
    info = details(map_id)
    data = http_client.fetch(f"{API}/maps/{info['id']}/data", limit=MAP_LIMIT, timeout=DOWNLOAD_TIMEOUT)
    if not is_msav(data):
        raise ValueError("MindustryTool returned something that is not a map file")
    in_game_name = files.save(_file_path(info["name"], info["id"]), data)
    if not in_game_name:
        raise ValueError("The map was downloaded but the server could not load it (it may need a mod)")

    return in_game_name


def install_and_play(map_id, mode):
    name = install(map_id)
    hosting.host(KIND_MAP, name, mode)

    return name
