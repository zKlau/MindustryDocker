"""Live game state and quick actions."""

import threading

from .. import settings
from ..server import server
from ..validation import js_string

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
    r.nextWave = Math.round(s.wavetime / 60);
    r.waveTimer = s.rules.waveTimer && s.rules.waves;
    r.paused = s.isPaused();
    r.enemies = s.enemies;
    r.players = Groups.player.size();
    r.mode = s.rules.mode().name();
    r.fps = Core.graphics.getFramesPerSecond();
    r.winWave = s.rules.winWave;
    r.minutes = Math.floor(s.tick / 3600);
  }
  return r;
})()"""

SAY_JS = "(function(){ Call.sendMessage('[scarlet][[Admin][] ' + MESSAGE); return true; })()"


def status():
    return {"running": server.alive(), **server.query(STATUS_JS)}


def pause(on):
    if on:
        server.send("pause on")
    else:
        server.send("pause off")


def next_wave():
    server.send("runwave")


def game_over():
    server.send("gameover")


def fill_core():
    server.send("fillitems")


def say(message):
    message = str(message).strip()[:200]
    if not message:
        raise ValueError("Message is empty")
    server.query(SAY_JS.replace("MESSAGE", js_string(message)))


def restart():
    """Save the world, then exit; the supervisor starts the server again and resumes the save."""
    worker = threading.Thread(target=server.exit, kwargs={"save_name": settings.SESSION_SAVE}, daemon=True)
    worker.start()
