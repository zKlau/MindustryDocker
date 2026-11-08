from .. import settings, state
from ..common.constants import KIND_MAP, KIND_SECTOR
from ..common.log import log
from ..common.validation import gamemode, map_name, sector
from ..server import server
from . import saves
from .maps import hosting

MODE_RESUME = "resume"
MODE_MAP = "map"
MODE_ENV = "env"
MODES = (MODE_RESUME, MODE_MAP, MODE_ENV)


def resume_save():
    candidates = [save for save in saves.list_all() if save["auto"]]
    if not candidates:
        return None

    return candidates[0]["name"]


def get():
    config = state.section(state.STARTUP)
    config["resumeSave"] = resume_save()

    return config


def _startup_map(kind, name):
    if kind == KIND_SECTOR:
        return sector(name)

    return map_name(name)


def update(values):
    mode = values.get("mode", MODE_RESUME)
    if mode not in MODES:
        raise ValueError("Invalid startup mode")
    kind = KIND_MAP
    if values.get("kind") == KIND_SECTOR:
        kind = KIND_SECTOR
    config = {"mode": mode, "kind": kind, "map": "", "gamemode": gamemode(values.get("gamemode"))}
    if mode == MODE_MAP:
        config["map"] = _startup_map(kind, values.get("map", ""))
    state.update(state.STARTUP, config)


def _uses_env():
    config = state.section(state.STARTUP)
    if config["mode"] == MODE_ENV:
        return True
    if config["mode"] == MODE_RESUME:
        return resume_save() is None

    return not config.get("map")


def start_commands():
    commands = [f"config port {settings.GAME_PORT}"]
    if settings.SERVER_NAME:
        commands.append(f"config name {settings.SERVER_NAME}")
    if _uses_env():
        commands += [command.strip() for command in settings.START_COMMANDS.split(",") if command.strip()]

    return commands


def on_server_ready():
    if _uses_env():
        return
    config = state.section(state.STARTUP)
    try:
        if config["mode"] == MODE_RESUME:
            name = resume_save()
            log(f"resuming save '{name}'")
            server.send(f"load {name}")
        else:
            log(f"hosting startup {config['kind']} '{config['map']}' ({config['gamemode']})")
            hosting.host(config["kind"], config["map"], config["gamemode"])
    except (RuntimeError, ValueError) as error:
        log(f"startup action failed ({error}); hosting a random map instead")
        server.send("host")
