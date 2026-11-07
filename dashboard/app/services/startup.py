"""What happens when the server process starts (container start, crash, or restart)."""

from .. import settings, state
from ..server import log, server
from ..validation import gamemode, map_name, sector
from . import maps, saves

MODES = ("resume", "map", "env")


def resume_save():
    """Newest of the shutdown save and Mindustry's autosaves (covers crashes too), or None."""
    candidates = [save for save in saves.list_all() if save["auto"]]
    if not candidates:
        return None
    return candidates[0]["name"]


def get():
    config = state.load()["startup"]
    config["resumeSave"] = resume_save()
    return config


def _startup_map(kind, name):
    if kind == "sector":
        return sector(name)
    return map_name(name)


def update(values):
    mode = values.get("mode", "resume")
    if mode not in MODES:
        raise ValueError("Invalid startup mode")
    kind = "map"
    if values.get("kind") == "sector":
        kind = "sector"
    config = {"mode": mode, "kind": kind, "map": "", "gamemode": gamemode(values.get("gamemode"))}
    if mode == "map":
        config["map"] = _startup_map(kind, values.get("map", ""))
    state.update("startup", config)


def _uses_env():
    config = state.load()["startup"]
    if config["mode"] == "env":
        return True
    if config["mode"] == "resume":
        return resume_save() is None
    return not config.get("map")


def start_commands():
    """Command-line commands for the java process. Always pins the internal port."""
    commands = [f"config port {settings.GAME_PORT}"]
    if settings.SERVER_NAME:
        commands.append(f"config name {settings.SERVER_NAME}")
    if _uses_env():
        commands += [command.strip() for command in settings.START_COMMANDS.split(",") if command.strip()]
    return commands


def on_server_ready():
    """Runs after every server start: resume the last session or host the chosen map."""
    if _uses_env():
        return
    config = state.load()["startup"]
    try:
        if config["mode"] == "resume":
            name = resume_save()
            log(f"resuming save '{name}'")
            server.send(f"load {name}")
        else:
            log(f"hosting startup {config['kind']} '{config['map']}' ({config['gamemode']})")
            maps.host(config["kind"], config["map"], config["gamemode"])
    except (RuntimeError, ValueError) as error:
        log(f"startup action failed ({error}); hosting a random map instead")
        server.send("host")
