from ...services import players
from ..router import get, post


@get("/api/players")
def list_players(req):
    return players.online()


@get("/api/players/bans")
def list_bans(req):
    return players.bans()


@post("/api/players/kick")
def kick(req):
    players.kick(req.field("id"))


@post("/api/players/ban")
def ban(req):
    players.ban(req.field("id"))


@post("/api/players/unban")
def unban(req):
    players.unban(req.field("id"))


@post("/api/players/admin")
def set_admin(req):
    players.set_admin(req.field("id"), bool(req.field("on", False)))
