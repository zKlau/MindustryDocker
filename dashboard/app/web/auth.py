import collections
import hmac
import secrets
import threading
import time

from .. import settings

SESSION_TTL = 7 * 24 * 3600
MAX_FAILURES = 5
LOCKOUT_SECONDS = 600
COOKIE = "mdash"
FAILED_LOGIN_DELAY_SECONDS = 1

_sessions = {}
_failures = collections.defaultdict(list)
_lock = threading.Lock()


class TooManyAttemptsError(Exception):
    pass


def enabled():
    return bool(settings.ADMIN_PASSWORD)


def login(password, client_ip):
    now = time.time()
    with _lock:
        _failures[client_ip] = [t for t in _failures[client_ip] if now - t < LOCKOUT_SECONDS]
        if len(_failures[client_ip]) >= MAX_FAILURES:
            raise TooManyAttemptsError()
    if enabled() and hmac.compare_digest(str(password).encode(), settings.ADMIN_PASSWORD.encode()):
        with _lock:
            _failures.pop(client_ip, None)
            token = secrets.token_urlsafe(32)
            _sessions[token] = now + SESSION_TTL

        return token
    with _lock:
        _failures[client_ip].append(now)
    time.sleep(FAILED_LOGIN_DELAY_SECONDS)

    return None


def logout(token):
    with _lock:
        _sessions.pop(token or "", None)


def valid(token):
    with _lock:
        expires = _sessions.get(token or "")
        if expires and expires > time.time():
            return True
        _sessions.pop(token or "", None)

        return False
