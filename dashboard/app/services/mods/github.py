from ... import settings
from ...common import http_client

GITHUB_API = "https://api.github.com"
RATE_LIMIT_STATUSES = (403, 429)
NO_RELEASE_STATUS = 404


def headers():
    result = {"Accept": "application/vnd.github+json"}
    if settings.GITHUB_TOKEN:
        result["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    return result


def _get(path):
    try:
        return http_client.fetch_json(f"{GITHUB_API}{path}", headers=headers())
    except http_client.HttpStatusError as error:
        if error.status in RATE_LIMIT_STATUSES:
            raise RuntimeError("GitHub rate limit reached. Try again later or set GITHUB_TOKEN.") from None
        raise


def _latest_release_assets(repository):
    try:
        release = _get(f"/repos/{repository}/releases/latest")
    except http_client.HttpStatusError as error:
        if error.status == NO_RELEASE_STATUS:
            return []
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


def download_source(mod):
    repository = mod["repo"]
    java = bool(mod.get("hasJava"))
    picked = _pick_asset(_latest_release_assets(repository), java)
    if picked is not None:
        return picked
    if java:
        raise ValueError("This Java mod has no .jar release to download")
    branch = _get(f"/repos/{repository}").get("default_branch", "master")

    return f"{GITHUB_API}/repos/{repository}/zipball/{branch}", ".zip"
