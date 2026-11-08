from ...services import server_config, startup
from ..router import get, post


@get("/api/config")
def get_config(req):
    return server_config.current()


@post("/api/config")
def set_config(req):
    server_config.update(req.field("values", {}))


@get("/api/startup")
def get_startup(req):
    return startup.get()


@post("/api/startup")
def set_startup(req):
    startup.update(req.json())
