"""API endpoints. Each one is a thin wrapper around a service function."""

from ..server import server
from ..services import (
    game,
    maps,
    mods,
    online_maps,
    online_mods,
    players,
    previews,
    rules,
    saves,
    server_config,
    startup,
)
from . import auth
from .router import ApiError, Response, route

UPLOAD_LIMIT = 100 * 1024 * 1024


# ---------------------------------------------------------------- session


@route("GET", "/api/session", public=True)
def session(req):
    return {"authed": req.handler.authed(), "enabled": auth.enabled()}


@route("POST", "/api/login", public=True)
def login(req):
    try:
        token = auth.login(req.json().get("password", ""), req.handler.client_ip())
    except auth.TooManyAttemptsError:
        raise ApiError(429, "Too many attempts. Try again in 10 minutes.") from None
    if not token:
        raise ApiError(403, "Wrong password")
    cookie = f"{auth.COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={auth.SESSION_TTL}"
    if req.handler.headers.get("X-Forwarded-Proto") == "https":
        cookie += "; Secure"
    return Response(b'{"ok": true}', headers={"Set-Cookie": cookie})


@route("POST", "/api/logout", public=True)
def logout(req):
    auth.logout(req.handler.cookie(auth.COOKIE))
    return Response(b'{"ok": true}', headers={"Set-Cookie": f"{auth.COOKIE}=; Path=/; Max-Age=0"})


# ---------------------------------------------------------------- game


@route("GET", "/api/status")
def status(req):
    return game.status()


@route("POST", "/api/game/pause")
def pause(req):
    game.pause(req.json().get("on"))


@route("POST", "/api/game/next-wave")
def next_wave(req):
    game.next_wave()


@route("POST", "/api/game/game-over")
def game_over(req):
    game.game_over()


@route("POST", "/api/game/fill-core")
def fill_core(req):
    game.fill_core()


@route("POST", "/api/game/say")
def say(req):
    game.say(req.json().get("message", ""))


@route("POST", "/api/game/restart")
def restart(req):
    game.restart()


# ---------------------------------------------------------------- maps


@route("GET", "/api/maps")
def list_maps(req):
    return maps.list_all()


@route("POST", "/api/maps/host")
def host_map(req):
    data = req.json()
    maps.host(data.get("kind", "map"), data.get("name", ""), data.get("mode", "survival"))


@route("POST", "/api/maps/next")
def next_map(req):
    maps.set_next(req.json().get("name", ""))


@route("POST", "/api/maps/upload")
def upload_map(req):
    maps.upload(req.arg("name"), req.body(UPLOAD_LIMIT))
    previews.forget_custom_maps()


@route("POST", "/api/maps/delete")
def delete_map(req):
    maps.delete_custom(req.json().get("name", ""))
    previews.forget_custom_maps()


@route("GET", "/api/maps/preview")
def map_preview(req):
    image = previews.get(req.arg("kind", "map"), req.arg("name"))
    return Response(image, content_type="image/png", headers={"Cache-Control": "private, max-age=86400"})


# ---------------------------------------------------------------- online maps (MindustryTool)


@route("GET", "/api/online/maps")
def search_online_maps(req):
    return online_maps.search(req.arg("q"), req.arg("sort", "popular"), req.arg("page", "0") or 0)


@route("GET", "/api/online/maps/details")
def online_map_details(req):
    return online_maps.details(req.arg("id"))


@route("GET", "/api/online/maps/preview")
def online_map_preview(req):
    image = online_maps.preview(req.arg("id"))
    return Response(image, content_type="image/png", headers={"Cache-Control": "private, max-age=86400"})


@route("POST", "/api/online/maps/install")
def install_online_map(req):
    data = req.json()
    if data.get("play"):
        name = online_maps.install_and_play(data.get("id", ""), data.get("mode", "survival"))
    else:
        name = online_maps.install(data.get("id", ""))
    return {"name": name}


# ---------------------------------------------------------------- rules


@route("GET", "/api/rules")
def get_rules(req):
    return rules.current()


@route("POST", "/api/rules")
def set_rules(req):
    rules.apply(req.json().get("values", {}))


@route("POST", "/api/rules/reset")
def reset_rules(req):
    rules.reset()


# ---------------------------------------------------------------- saves


@route("GET", "/api/saves")
def list_saves(req):
    return saves.list_all()


@route("POST", "/api/saves/save")
def save_game(req):
    saves.save(req.json().get("name", ""))


@route("POST", "/api/saves/load")
def load_save(req):
    saves.load(req.json().get("name", ""))


@route("POST", "/api/saves/delete")
def delete_save(req):
    saves.delete(req.json().get("name", ""))


@route("POST", "/api/saves/upload")
def upload_save(req):
    saves.upload(req.arg("name"), req.body(UPLOAD_LIMIT))


@route("GET", "/api/saves/download")
def download_save(req):
    f = saves.path(req.arg("name"))
    if not f.exists():
        raise ApiError(404, "Save not found")
    return Response(
        f.read_bytes(),
        content_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{f.name}"'},
    )


# ---------------------------------------------------------------- players


@route("GET", "/api/players")
def list_players(req):
    return players.online()


@route("GET", "/api/players/bans")
def list_bans(req):
    return players.bans()


@route("POST", "/api/players/kick")
def kick(req):
    players.kick(req.json().get("id", ""))


@route("POST", "/api/players/ban")
def ban(req):
    players.ban(req.json().get("id", ""))


@route("POST", "/api/players/unban")
def unban(req):
    players.unban(req.json().get("id", ""))


@route("POST", "/api/players/admin")
def set_admin(req):
    data = req.json()
    players.set_admin(data.get("id", ""), bool(data.get("on")))


# ---------------------------------------------------------------- settings


@route("GET", "/api/config")
def get_config(req):
    return server_config.current()


@route("POST", "/api/config")
def set_config(req):
    server_config.update(req.json().get("values", {}))


@route("GET", "/api/startup")
def get_startup(req):
    return startup.get()


@route("POST", "/api/startup")
def set_startup(req):
    startup.update(req.json())


# ---------------------------------------------------------------- mods


@route("GET", "/api/mods")
def list_mods(req):
    return mods.list_all()


@route("POST", "/api/mods/upload")
def upload_mod(req):
    mods.upload(req.arg("name"), req.body(UPLOAD_LIMIT))


@route("POST", "/api/mods/delete")
def delete_mod(req):
    mods.delete(req.json().get("file", ""))


@route("GET", "/api/online/mods")
def search_online_mods(req):
    only_compatible = req.arg("compatible", "1") != "0"
    return online_mods.search(
        req.arg("q"), req.arg("sort", "stars"), req.arg("page", "0") or 0, only_compatible
    )


@route("POST", "/api/online/mods/install")
def install_online_mod(req):
    return online_mods.install(req.json().get("repo", ""))


# ---------------------------------------------------------------- console


@route("GET", "/api/logs")
def logs(req):
    lines, last = server.logs_since(int(req.arg("since", "0") or 0))
    return {"lines": lines[-1000:], "last": last}


@route("POST", "/api/console")
def console(req):
    if not server.send(str(req.json().get("command", ""))):
        raise ApiError(503, "Server is not running")
