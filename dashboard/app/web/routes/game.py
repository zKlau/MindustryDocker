from ...services import game
from ..router import get, post


@get("/api/status")
def status(req):
    return game.status()


@post("/api/game/pause")
def pause(req):
    game.pause(req.field("on"))


@post("/api/game/next-wave")
def next_wave(req):
    game.next_wave()


@post("/api/game/game-over")
def game_over(req):
    game.game_over()


@post("/api/game/fill-core")
def fill_core(req):
    game.fill_core()


@post("/api/game/say")
def say(req):
    game.say(req.field("message"))


@post("/api/game/restart")
def restart(req):
    game.restart()
