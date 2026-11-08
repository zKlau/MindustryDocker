import itertools
import queue
import threading


class PendingQueries:
    def __init__(self):
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self._waiting = {}

    def open(self):
        answer = queue.Queue()
        with self._lock:
            query_id = next(self._ids)
            self._waiting[query_id] = answer

        return query_id, answer

    def cancel(self, query_id):
        with self._lock:
            self._waiting.pop(query_id, None)

    def answer(self, query_id, payload):
        with self._lock:
            answer = self._waiting.pop(query_id, None)
        if answer is not None:
            answer.put(payload)
