from ...common.log import log
from ...common.threads import run_in_background
from ...common.validation import network_uuid
from . import password, whitelist
from .constants import ACCESS_MARKER, LOGIN_COMMAND, LOGIN_FAILED, WHITELIST_REQUEST


def on_server_ready():
    try:
        password.install()
    except RuntimeError as error:
        log(f"could not install join protection: {error}")


def filter_line(line):
    marker = ACCESS_MARKER.search(line)
    if marker:
        run_in_background(_on_login_event, *marker.groups())

        return None
    request = WHITELIST_REQUEST.search(line)
    if request:
        run_in_background(whitelist.add_request, *request.groups())

    return LOGIN_COMMAND.sub(r"\1 ****", line)


def _on_login_event(kind, player_id, name):
    player_id = network_uuid(player_id)
    if player_id is None:
        return
    if kind == LOGIN_FAILED:
        log(f"wrong join password from {name}")

        return
    log(f"{name} logged in with the join password")
    password.remember(player_id)
