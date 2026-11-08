from ...common import http_client
from ...common.constants import MAX_SEARCH_QUERY_LENGTH
from ...common.validation import is_zip, repo, text
from . import catalog, github, installed

PAGE_SIZE = 25
DOWNLOAD_TIMEOUT = 120


def search(query="", sort=catalog.DEFAULT_SORT, page=0, only_compatible=True):
    build = catalog.server_build()
    query = text(query, MAX_SEARCH_QUERY_LENGTH).lower()
    entries = [m for m in catalog.mods() if catalog.matches(m, query)]
    if only_compatible:
        entries = [m for m in entries if catalog.compatible(m, build)]
    entries = catalog.sort(entries, sort)
    start = max(0, int(page)) * PAGE_SIZE
    installed_stems = {path.stem.lower() for path in installed.files()}

    return {
        "mods": [catalog.describe(m, build, installed_stems) for m in entries[start : start + PAGE_SIZE]],
        "hasMore": start + PAGE_SIZE < len(entries),
        "total": len(entries),
        "serverBuild": build,
    }


def install(repository):
    mod = catalog.find(repo(repository))
    url, extension = github.download_source(mod)
    data = http_client.fetch(url, headers=github.headers(), timeout=DOWNLOAD_TIMEOUT)
    if not is_zip(data):
        raise ValueError("The download is not a .jar or .zip file")

    return {"file": installed.save(catalog.file_stem(mod), extension, data)}
