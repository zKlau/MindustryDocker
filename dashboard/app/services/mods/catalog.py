import threading
import time

from ...common import http_client
from ...common.text import first_line, slugify, strip_colors
from ...server import server

MODS_LIST_URL = "https://raw.githubusercontent.com/Anuken/MindustryMods/master/mods.json"
CACHE_SECONDS = 3600
OLDEST_LOADABLE_MOD_BUILD = 136
DEFAULT_SORT = "stars"
SORTS = (DEFAULT_SORT, "updated", "name")
SEARCHED_FIELDS = ("name", "repo", "author", "description")
MAX_DESCRIPTION_LENGTH = 300
STEM_LENGTH = 60

_cache = {"time": 0.0, "mods": []}
_cache_lock = threading.Lock()


def mods():
    with _cache_lock:
        if time.time() - _cache["time"] > CACHE_SECONDS or not _cache["mods"]:
            _cache["mods"] = http_client.fetch_json(MODS_LIST_URL)
            _cache["time"] = time.time()

        return _cache["mods"]


def find(repository):
    for mod in mods():
        if mod["repo"].lower() == repository.lower():
            return mod
    raise ValueError("That mod is not in the official mod list")


def server_build():
    try:
        return int(server.query("Version.build"))
    except (RuntimeError, ValueError, TypeError):
        return None


def _min_version(mod):
    try:
        return float(mod.get("minGameVersion") or 0)
    except ValueError:
        return 0.0


def compatible(mod, build):
    minimum = _min_version(mod)
    if minimum < OLDEST_LOADABLE_MOD_BUILD:
        return False

    return build is None or minimum <= build


def file_stem(mod):
    name = mod.get("internalName") or mod["repo"].split("/")[-1]

    return slugify(name, "-", STEM_LENGTH, "mod")


def matches(mod, query):
    if not query:
        return True
    text = " ".join(str(mod.get(key, "")) for key in SEARCHED_FIELDS)

    return query in text.lower()


def sort(entries, order):
    if order == "updated":
        return sorted(entries, key=lambda m: m.get("lastUpdated", ""), reverse=True)
    if order == "name":
        return sorted(entries, key=lambda m: str(m.get("name", "")).lower())

    return sorted(entries, key=lambda m: m.get("stars", 0), reverse=True)


def describe(mod, build, installed_stems):
    return {
        "repo": mod["repo"],
        "name": strip_colors(mod.get("name")) or mod["repo"],
        "author": first_line(mod.get("author")),
        "description": " ".join(strip_colors(mod.get("description")).split())[:MAX_DESCRIPTION_LENGTH],
        "stars": mod.get("stars", 0),
        "version": first_line(mod.get("version")),
        "minGameVersion": str(mod.get("minGameVersion", "")),
        "lastUpdated": mod.get("lastUpdated", ""),
        "java": bool(mod.get("hasJava")),
        "compatible": compatible(mod, build),
        "installed": file_stem(mod).lower() in installed_stems,
    }
