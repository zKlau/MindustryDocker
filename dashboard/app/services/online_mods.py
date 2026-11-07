"""Browse and install mods from the official Mindustry mod list (the one the in-game mod browser uses).

Downloads come from each mod's GitHub releases, like the game does: Java mods use the release
.jar, script/content mods use a release .zip or else a zip of the repository.
"""

import re
import threading
import time

from .. import http_client, settings
from ..server import server
from ..validation import repo, strip_colors
from . import mods

MODS_LIST_URL = "https://raw.githubusercontent.com/Anuken/MindustryMods/master/mods.json"
GITHUB_API = "https://api.github.com"
CACHE_SECONDS = 3600
PAGE_SIZE = 25
OLDEST_SUPPORTED_BUILD = 136  # the game refuses mods made for older versions
SORTS = ("stars", "updated", "name")

_cache = {"time": 0.0, "mods": []}
_cache_lock = threading.Lock()


def _catalog():
    with _cache_lock:
        if time.time() - _cache["time"] > CACHE_SECONDS or not _cache["mods"]:
            _cache["mods"] = http_client.fetch_json(MODS_LIST_URL)
            _cache["time"] = time.time()
        return _cache["mods"]


def _server_build():
    try:
        return int(server.query("Version.build"))
    except (RuntimeError, ValueError, TypeError):
        return None


def _min_version(mod):
    try:
        return float(mod.get("minGameVersion") or 0)
    except ValueError:
        return 0.0


def _compatible(mod, build):
    minimum = _min_version(mod)
    if minimum < OLDEST_SUPPORTED_BUILD:
        return False
    return build is None or minimum <= build


def _file_stem(mod):
    name = mod.get("internalName") or mod["repo"].split("/")[-1]
    return re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-")[:60] or "mod"


def _installed_stems():
    if not settings.MODS_DIR.exists():
        return set()
    return {
        path.stem.lower() for path in settings.MODS_DIR.iterdir() if path.suffix.lower() in mods.EXTENSIONS
    }


def _matches(mod, query):
    if not query:
        return True
    text = " ".join(str(mod.get(key, "")) for key in ("name", "repo", "author", "description"))
    return query in text.lower()


def _sorted(entries, sort):
    if sort == "updated":
        return sorted(entries, key=lambda m: m.get("lastUpdated", ""), reverse=True)
    if sort == "name":
        return sorted(entries, key=lambda m: str(m.get("name", "")).lower())
    return sorted(entries, key=lambda m: m.get("stars", 0), reverse=True)


def _first_line(text):
    lines = strip_colors(text).splitlines() or [""]
    return lines[0].strip()


def _describe(mod, build, installed):
    return {
        "repo": mod["repo"],
        "name": strip_colors(mod.get("name")) or mod["repo"],
        "author": _first_line(mod.get("author")),
        "description": " ".join(strip_colors(mod.get("description")).split())[:300],
        "stars": mod.get("stars", 0),
        "version": _first_line(mod.get("version")),
        "minGameVersion": str(mod.get("minGameVersion", "")),
        "lastUpdated": mod.get("lastUpdated", ""),
        "java": bool(mod.get("hasJava")),
        "compatible": _compatible(mod, build),
        "installed": _file_stem(mod).lower() in installed,
    }


def search(query="", sort="stars", page=0, only_compatible=True):
    build = _server_build()
    query = str(query).strip().lower()[:60]
    entries = [m for m in _catalog() if _matches(m, query)]
    if only_compatible:
        entries = [m for m in entries if _compatible(m, build)]
    entries = _sorted(entries, sort)
    start = max(0, int(page)) * PAGE_SIZE
    installed = _installed_stems()
    page_entries = entries[start : start + PAGE_SIZE]
    return {
        "mods": [_describe(m, build, installed) for m in page_entries],
        "hasMore": start + PAGE_SIZE < len(entries),
        "total": len(entries),
        "serverBuild": build,
    }


def _github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return headers


def _github(path):
    try:
        return http_client.fetch_json(f"{GITHUB_API}{path}", headers=_github_headers())
    except http_client.HttpStatusError as error:
        if error.status in (403, 429):
            raise RuntimeError("GitHub rate limit reached. Try again later or set GITHUB_TOKEN.") from None
        raise


def _latest_release_assets(repository):
    try:
        release = _github(f"/repos/{repository}/releases/latest")
    except http_client.HttpStatusError as error:
        if error.status == 404:
            return []  # no releases
        raise
    return release.get("assets") or []


def _pick_asset(assets, java):
    preferred = (".zip", ".jar")
    if java:
        preferred = (".jar", ".zip")
    for extension in preferred:
        for asset in assets:
            if asset["name"].lower().endswith(extension):
                return asset["browser_download_url"], extension
    return None


def _download_source(mod):
    """(url, extension) to download for a mod, following the game's own rules."""
    repository = mod["repo"]
    picked = _pick_asset(_latest_release_assets(repository), bool(mod.get("hasJava")))
    if picked is not None:
        return picked
    if mod.get("hasJava"):
        raise ValueError("This Java mod has no .jar release to download")
    branch = _github(f"/repos/{repository}").get("default_branch", "master")
    return f"{GITHUB_API}/repos/{repository}/zipball/{branch}", ".zip"


def _find(repository):
    for mod in _catalog():
        if mod["repo"].lower() == repository.lower():
            return mod
    raise ValueError("That mod is not in the official mod list")


def install(repository):
    """Download a mod into config/mods. It loads after the next server restart."""
    mod = _find(repo(repository))
    url, extension = _download_source(mod)
    data = http_client.fetch(url, headers=_github_headers(), timeout=120)
    if not data.startswith(b"PK"):
        raise ValueError("The download is not a .jar or .zip file")
    settings.MODS_DIR.mkdir(parents=True, exist_ok=True)
    stem = _file_stem(mod)
    for old in settings.MODS_DIR.glob(f"{stem}.*"):
        old.unlink()
    target = settings.MODS_DIR / f"{stem}{extension}"
    target.write_bytes(data)
    return {"file": target.name}
