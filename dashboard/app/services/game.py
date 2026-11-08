from .. import settings
from ..common.constants import TICKS_PER_SECOND
from ..common.js import fill, literal
from ..common.text import on_off
from ..common.threads import run_in_background
from ..common.validation import text
from ..server import server
from .resources import CORE_JS, POWER_JS, core_items, power_totals

MAX_MESSAGE_LENGTH = 200

STATUS_JS = """(function(){
  var s = Vars.state;
  var r = {
    hosting: !s.isMenu(),
    heapMB: Math.round(Core.app.getJavaHeap() / 1048576),
    playerLimit: Vars.netServer.admins.getPlayerLimit()
  };
  if (!s.isMenu()) {
    r.map = s.map.plainName();
    r.planet = s.rules.planet.name;
    r.wave = s.wave;
    r.nextWave = Math.round(s.wavetime / TICKS);
    r.waveTimer = s.rules.waveTimer && s.rules.waves;
    r.paused = s.isPaused();
    r.enemies = s.enemies;
    r.players = Groups.player.size();
    r.mode = s.rules.mode().name();
    r.fps = Core.graphics.getFramesPerSecond();
    r.winWave = s.rules.winWave;
    r.minutes = Math.floor(s.tick / (TICKS * 60));
    r.tick = s.tick;
    r.core = CORE;
    r.power = POWER;
  }
  return r;
})()"""

SAY_JS = "(function(){ Call.sendMessage('[scarlet][[Admin][] ' + MESSAGE); return true; })()"


def status():
    result = server.query(fill(STATUS_JS, TICKS=TICKS_PER_SECOND, CORE=CORE_JS, POWER=POWER_JS))
    if result.get("hosting"):
        result["core"] = core_items(result.get("core"), result["map"], result.pop("tick"))
        result["power"] = power_totals(result.get("power"))

    return {"running": server.alive(), **result}


def pause(on):
    server.send(f"pause {on_off(on)}")


def next_wave():
    server.send("runwave")


def game_over():
    server.send("gameover")


def fill_core():
    server.send("fillitems")


def say(message):
    message = text(message, MAX_MESSAGE_LENGTH)
    if not message:
        raise ValueError("Message is empty")
    server.query(fill(SAY_JS, MESSAGE=literal(message)))


def restart():
    run_in_background(server.exit, save_name=settings.SESSION_SAVE)
