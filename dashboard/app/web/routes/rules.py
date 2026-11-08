from ...services import rules
from ..router import get, post


@get("/api/rules")
def get_rules(req):
    return rules.current()


@post("/api/rules")
def set_rules(req):
    rules.apply(req.field("values", {}))


@post("/api/rules/reset")
def reset_rules(req):
    rules.reset()
