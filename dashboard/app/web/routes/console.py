from ...server import server
from ..router import ApiError, get, post

MAX_LOG_LINES = 1000


@get("/api/logs")
def logs(req):
    lines, last = server.logs_since(req.int_arg("since"))

    return {"lines": lines[-MAX_LOG_LINES:], "last": last}


@post("/api/console")
def console(req):
    if not server.send(str(req.field("command"))):
        raise ApiError(503, "Server is not running")
