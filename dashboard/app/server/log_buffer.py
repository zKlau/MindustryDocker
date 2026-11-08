import collections
import threading
import time

from .constants import DEFAULT_LOG_WAIT_SECONDS, LOG_LINES_KEPT, LOG_POLL_SECONDS


class LogBuffer:
    def __init__(self, max_lines=LOG_LINES_KEPT):
        self._lock = threading.Lock()
        self._lines = collections.deque(maxlen=max_lines)
        self.seq = 0

    def append(self, line):
        with self._lock:
            self.seq += 1
            self._lines.append((self.seq, line))

    def since(self, since):
        with self._lock:
            return [{"n": n, "t": t} for n, t in self._lines if n > since], self.seq

    def wait_for(self, text, since=None, timeout=DEFAULT_LOG_WAIT_SECONDS):
        start_seq = since
        if start_seq is None:
            start_seq = self.seq
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if any(n > start_seq and text in t for n, t in self._lines):
                    return True
            time.sleep(LOG_POLL_SECONDS)

        return False
