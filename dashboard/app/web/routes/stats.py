from ...services.stats import leaderboard
from ..router import get, post


@get("/api/stats")
def get_leaderboard(req):
    return leaderboard.leaderboard()


@post("/api/stats/remove")
def remove_stats(req):
    leaderboard.remove(req.field("id"))


@post("/api/stats/reset")
def reset_stats(req):
    leaderboard.reset()
