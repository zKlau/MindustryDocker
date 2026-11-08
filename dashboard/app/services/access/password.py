from ...common.js import fill, literal
from ...server import server
from .. import players
from . import entries
from .constants import INSTALL_TIMEOUT, LOGIN_TIMEOUT, MAX_PASSWORD_LENGTH
from .scripts import CONFIGURE_JS, INSTALL_JS


def install():
    server.query(fill(INSTALL_JS, TIMEOUT=LOGIN_TIMEOUT), timeout=INSTALL_TIMEOUT)
    push_settings()


def push_settings():
    access = entries.load()
    remembered = {player_id: True for player_id in access["remembered"]}
    script = fill(
        CONFIGURE_JS,
        ENABLED=literal(bool(access["passwordEnabled"])),
        PASSWORD=literal(str(access["password"])),
        REMEMBERED=literal(remembered),
    )
    server.query(script)


def remember(player_id):
    def add(access):
        if player_id not in access["remembered"]:
            access["remembered"].append(player_id)

    entries.modify(add)


def _validate(password):
    password = str(password)
    if len(password) > MAX_PASSWORD_LENGTH or any(c.isspace() for c in password):
        raise ValueError(f"Use up to {MAX_PASSWORD_LENGTH} characters without spaces")

    return password


def set_password(enabled, password=None):
    online_ids = [player["id"] for player in players.online_brief()]

    def change(access):
        if password:
            access["password"] = _validate(password)
            access["remembered"] = []
        if enabled and not access["password"]:
            raise ValueError("Set a password first")
        if enabled and not access["passwordEnabled"]:
            access["remembered"] = sorted(set(access["remembered"]) | set(online_ids))
        access["passwordEnabled"] = bool(enabled)

    entries.modify(change)
    if enabled:
        _keep_passwords_out_of_game_log_files()
    push_settings()


def _keep_passwords_out_of_game_log_files():
    server.send("config logCommands false")
    server.send("config logging false")


def forget_logins():
    entries.modify(lambda access: access.update(remembered=[]))
    push_settings()
