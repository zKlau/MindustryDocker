from ...services.access import password, status, whitelist
from ..router import get, post


@get("/api/access")
def access_status(req):
    return status.status()


@post("/api/access/password")
def set_join_password(req):
    password.set_password(bool(req.field("enabled", False)), req.field("password") or None)


@post("/api/access/forget")
def forget_logins(req):
    password.forget_logins()


@post("/api/access/whitelist")
def set_whitelist(req):
    whitelist.set_enabled(bool(req.field("enabled", False)))


@post("/api/access/whitelist/approve")
def approve_player(req):
    whitelist.approve(req.field("id"), req.field("name"))


@post("/api/access/whitelist/remove")
def remove_player(req):
    whitelist.remove(req.field("id"))


@post("/api/access/whitelist/dismiss")
def dismiss_request(req):
    whitelist.dismiss(req.field("id"))
