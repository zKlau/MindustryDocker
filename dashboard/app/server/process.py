import json
import queue
import subprocess
import threading
import time

from .. import settings
from ..common.log import log
from ..common.threads import run_in_background
from .constants import (
    ANSI,
    DEFAULT_LOG_WAIT_SECONDS,
    DEFAULT_QUERY_TIMEOUT,
    EXIT_TIMEOUT_SECONDS,
    HOSTING_JS,
    QUERY_MARKER,
    QUERY_PREFIX,
    READY_LINE,
    RESTART_DELAY_SECONDS,
    SAVE_TIMEOUT_SECONDS,
    SAVED_LINE,
)
from .log_buffer import LogBuffer
from .pending_queries import PendingQueries


def _single_line(text):
    return " ".join(text.split())


class MindustryServer:
    def __init__(self):
        self.proc = None
        self._write_lock = threading.Lock()
        self._queries = PendingQueries()
        self._log = LogBuffer()
        self.ready = threading.Event()
        self.stopping = False
        self.on_ready = []
        self.line_filters = []

    def _start(self, start_commands):
        args = ["java", *settings.JAVA_OPTS, "-jar", settings.SERVER_JAR]
        if start_commands:
            args.append(",".join(start_commands))
        log(f"starting Mindustry: {', '.join(start_commands) or '(no start commands)'}")
        self.ready.clear()
        self.proc = subprocess.Popen(
            args,
            cwd=settings.DATA_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        run_in_background(self._read_output, self.proc)

    def run_forever(self, start_commands_fn):
        while True:
            self._start(start_commands_fn())
            code = self.proc.wait()
            if self.stopping:
                return code
            log(f"Mindustry exited with code {code}; restarting in {RESTART_DELAY_SECONDS}s")
            time.sleep(RESTART_DELAY_SECONDS)

    def shutdown(self, save_name=None):
        self.stopping = True
        self.exit(save_name)

    def exit(self, save_name=None):
        if not self.alive():
            return
        if save_name:
            self._save_before_exit(save_name)
        self.send("exit")
        try:
            self.proc.wait(timeout=EXIT_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self.proc.terminate()

    def _save_before_exit(self, save_name):
        try:
            if self.hosting(timeout=3):
                since = self._log.seq
                self.send(f"save {save_name}")
                self.wait_for_log(SAVED_LINE, since=since, timeout=SAVE_TIMEOUT_SECONDS)
        except RuntimeError:
            pass

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def _read_output(self, proc):
        for raw in proc.stdout:
            line = ANSI.sub("", raw.rstrip("\r\n"))
            marker = QUERY_MARKER.search(line)
            if marker:
                self._queries.answer(int(marker.group(1)), marker.group(2))
                continue
            line = self._apply_filters(line)
            if line is not None:
                self._record(line)

    def _apply_filters(self, line):
        for line_filter in self.line_filters:
            line = line_filter(line)
            if line is None:
                return None

        return line

    def _record(self, line):
        print(line, flush=True)
        self._log.append(line)
        if READY_LINE in line and not self.ready.is_set():
            self.ready.set()
            for callback in self.on_ready:
                run_in_background(callback)

    def logs_since(self, since):
        return self._log.since(since)

    def wait_for_log(self, text, since=None, timeout=DEFAULT_LOG_WAIT_SECONDS):
        return self._log.wait_for(text, since=since, timeout=timeout)

    def send(self, command):
        command = command.replace("\r", " ").replace("\n", " ").strip()
        if not command or not self.alive():
            return False
        try:
            with self._write_lock:
                self.proc.stdin.write(command + "\n")
                self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            return False

        return True

    def query(self, js_expression, timeout=DEFAULT_QUERY_TIMEOUT):
        query_id, answer = self._queries.open()
        if not self.send(f'js "{QUERY_PREFIX}:{query_id}:" + JSON.stringify({_single_line(js_expression)})'):
            self._queries.cancel(query_id)
            raise RuntimeError("server is not running")
        try:
            return json.loads(answer.get(timeout=timeout))
        except queue.Empty:
            self._queries.cancel(query_id)
            raise RuntimeError("server did not answer (still starting?)") from None

    def query_or(self, default, js_expression, timeout=DEFAULT_QUERY_TIMEOUT):
        try:
            return self.query(js_expression, timeout=timeout)
        except RuntimeError:
            return default

    def hosting(self, timeout=DEFAULT_QUERY_TIMEOUT):
        return bool(self.query(HOSTING_JS, timeout=timeout))
