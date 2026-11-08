import re

LOGIN_TIMEOUT = 60
MAX_REQUESTS = 50
MAX_PASSWORD_LENGTH = 64
MAX_NAME_LENGTH = 60
INSTALL_TIMEOUT = 15

ACCESS_MARKER = re.compile(r"@@ACCESS:(login|failed):([^:]+):(.*)$")
WHITELIST_REQUEST = re.compile(r"whitelist add (\S+) to whitelist the player '(.*)'")
LOGIN_COMMAND = re.compile(r"(/login)\s+\S.*", re.IGNORECASE)
LOGIN_FAILED = "failed"
