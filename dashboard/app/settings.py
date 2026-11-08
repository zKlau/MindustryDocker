import os
import pathlib

DATA_DIR = pathlib.Path(os.environ.get("MINDUSTRY_DATA", "/data"))
SERVER_JAR = os.environ.get("MINDUSTRY_JAR", "/opt/mindustry/server-release.jar")
JAVA_OPTS = os.environ.get("JAVA_OPTS", "").split()
START_COMMANDS = os.environ.get("MINDUSTRY_START_COMMANDS", "config port 6567,host")
SERVER_NAME = os.environ.get("MINDUSTRY_SERVER_NAME", "")
CONTAINER_GAME_PORT = 6567

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HTTP_PORT = int(os.environ.get("DASHBOARD_INTERNAL_PORT", "8080"))
APP_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = APP_DIR.parent / "static"
BLOCK_COLORS_FILE = APP_DIR / "data" / "block_colors.json"

CONFIG_DIR = DATA_DIR / "config"
SAVES_DIR = CONFIG_DIR / "saves"
MAPS_DIR = CONFIG_DIR / "maps"
MODS_DIR = CONFIG_DIR / "mods"

STATE_DIR = DATA_DIR / "dashboard"
STATE_FILE = STATE_DIR / "state.json"
STATS_FILE = STATE_DIR / "stats.json"
PREVIEW_DIR = STATE_DIR / "previews"
ONLINE_PREVIEW_DIR = STATE_DIR / "online-previews"

SESSION_SAVE = "last-session"
