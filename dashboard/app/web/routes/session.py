from .. import auth, cookies, responses
from ..router import ApiError, get, post


@get("/api/session", public=True)
def session(req):
    return {"authed": req.handler.authed(), "enabled": auth.enabled()}


@post("/api/login", public=True)
def login(req):
    try:
        token = auth.login(req.field("password"), req.handler.client_ip())
    except auth.TooManyAttemptsError:
        minutes = auth.LOCKOUT_SECONDS // 60
        raise ApiError(429, f"Too many attempts. Try again in {minutes} minutes.") from None
    if not token:
        raise ApiError(403, "Wrong password")
    cookie = cookies.session_cookie(auth.COOKIE, token, auth.SESSION_TTL, req.handler.is_https())

    return responses.ok({"Set-Cookie": cookie})


@post("/api/logout", public=True)
def logout(req):
    auth.logout(req.handler.cookie(auth.COOKIE))

    return responses.ok({"Set-Cookie": cookies.expired_cookie(auth.COOKIE)})
