from . import entries, whitelist
from .constants import LOGIN_TIMEOUT


def status():
    access = entries.load()

    return {
        "passwordEnabled": access["passwordEnabled"],
        "hasPassword": bool(access["password"]),
        "rememberedCount": len(access["remembered"]),
        "loginTimeout": LOGIN_TIMEOUT,
        "whitelistEnabled": whitelist.enabled(),
        "approved": access["approved"],
        "requests": access["requests"],
    }
