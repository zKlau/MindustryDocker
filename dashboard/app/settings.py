"""Configuration from environment variables, plus well-known paths."""

import os
import pathlib

# Process / environment
DATA_DIR = pathlib.Path(os.environ.get("MINDUSTRY_DATA", "/data"))
SERVER_JAR = os.environ.get("MINDUSTRY_JAR", "/opt/mindustry/server-release.jar")
JAVA_OPTS = os.environ.get("JAVA_OPTS", "").split()
START_COMMANDS = os.environ.get("MINDUSTRY_START_COMMANDS", "config port 6567,host")
SERVER_NAME = os.environ.get("MINDUSTRY_SERVER_NAME", "")
GAME_PORT = 6567  # fixed inside the container; the public port is mapped by Docker

# Dashboard
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # optional, raises GitHub's 60 requests/hour limit
HTTP_PORT = int(os.environ.get("DASHBOARD_INTERNAL_PORT", "8080"))
STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "static"

# Mindustry data layout (the server uses ./config relative to its working dir)
CONFIG_DIR = DATA_DIR / "config"
SAVES_DIR = CONFIG_DIR / "saves"
MAPS_DIR = CONFIG_DIR / "maps"
MODS_DIR = CONFIG_DIR / "mods"

# Files owned by the dashboard
STATE_DIR = DATA_DIR / "dashboard"
STATE_FILE = STATE_DIR / "state.json"

# Save written on shutdown/restart so the next start can continue the same world
SESSION_SAVE = "last-session"
