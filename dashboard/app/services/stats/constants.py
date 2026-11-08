import re

TICK_SECONDS = 60
MAX_COUNTED_GAP_SECONDS = 2 * TICK_SECONDS
INSTALL_TIMEOUT = 15
TOP_COUNT = 5

PLAYTIME = "playtime"
SESSIONS = "sessions"
SCRIPT_COUNTERS = ("built", "broken", "waves")

CATEGORIES = {
    PLAYTIME: "Playtime",
    SESSIONS: "Sessions",
    "built": "Blocks built",
    "broken": "Blocks broken",
    "waves": "Waves survived",
}

STATS_MARKER = re.compile(r"@@STATS:(join|stats|top):([^:]+):(.*)$")
MARKER_JOIN = "join"
MARKER_STATS = "stats"

NO_STATS_MESSAGE = "[scarlet]No stats yet."
