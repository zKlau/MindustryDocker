"""Runs the Mindustry server process and talks to its console.

- Commands are written to the server's stdin.
- Structured data is read back by evaluating JavaScript with the server's `js`
  command; results are tagged with a marker so they never show up in the log.
"""

import collections
import itertools
import json
import queue
import re
import subprocess
import threading
import time

from . import settings

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
MARKER = re.compile(r"@@DASH:(\d+):(.*)$")
READY_LINE = "Server loaded."


def log(msg):
    print(f"[dashboard] {msg}", flush=True)


class MindustryServer:
    def __init__(self):
        self.proc = None
        self._log_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._ids = itertools.count(1)
        self._pending = {}
        self.logs = collections.deque(maxlen=3000)
        self.seq = 0
        self.ready = threading.Event()
        self.stopping = False
        self.on_ready = []  # callbacks run (in a thread) each time the server finishes loading
        # Callables run on every output line: return the (possibly edited) line, or None to hide it.
        self.line_filters = []

    # ------------------------------------------------------------ lifecycle

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
        threading.Thread(target=self._read_output, args=(self.proc,), daemon=True).start()

    def run_forever(self, start_commands_fn):
        """Start the server and restart it whenever it exits, until shutdown() is called."""
        while True:
            self._start(start_commands_fn())
            code = self.proc.wait()
            if self.stopping:
                return code
            log(f"Mindustry exited with code {code}; restarting in 3s")
            time.sleep(3)

    def shutdown(self, save_name=None):
        """Optionally save the world, then stop the server for good."""
        self.stopping = True
        self.exit(save_name)

    def exit(self, save_name=None):
        """Save (if hosting) and exit the process. run_forever() restarts it unless stopping."""
        if not self.alive():
            return
        if save_name:
            try:
                if self.query("!Vars.state.isMenu()", timeout=3):
                    since = self.seq
                    self.send(f"save {save_name}")
                    self.wait_for_log("Saved to", since=since, timeout=10)
            except RuntimeError:
                pass
        self.send("exit")
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.terminate()

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    # ------------------------------------------------------------ output

    def _read_output(self, proc):
        for raw in proc.stdout:
            line = ANSI.sub("", raw.rstrip("\r\n"))
            marker = MARKER.search(line)
            if marker:
                q = self._pending.pop(int(marker.group(1)), None)
                if q:
                    q.put(marker.group(2))
                continue
            line = self._apply_filters(line)
            if line is None:
                continue
            print(line, flush=True)
            with self._log_lock:
                self.seq += 1
                self.logs.append((self.seq, line))
            if READY_LINE in line and not self.ready.is_set():
                self.ready.set()
                for callback in self.on_ready:
                    threading.Thread(target=callback, daemon=True).start()

    def _apply_filters(self, line):
        for line_filter in self.line_filters:
            line = line_filter(line)
            if line is None:
                return None
        return line

    def logs_since(self, since):
        with self._log_lock:
            return [{"n": n, "t": t} for n, t in self.logs if n > since], self.seq

    def wait_for_log(self, text, since=None, timeout=10.0):
        start_seq = since
        if start_seq is None:
            start_seq = self.seq
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._log_lock:
                if any(n > start_seq and text in t for n, t in self.logs):
                    return True
            time.sleep(0.2)
        return False

    # ------------------------------------------------------------ input

    def send(self, command):
        """Write one console command. Newlines are stripped so input can't inject extra commands."""
        command = command.replace("\r", " ").replace("\n", " ").strip()
        if not command or not self.alive():
            return False
        try:
            with self._write_lock:
                self.proc.stdin.write(command + "\n")
                self.proc.stdin.flush()
            return True
        except (BrokenPipeError, OSError):
            return False

    def query(self, js_expression, timeout=5.0):
        """Evaluate a JS expression inside the server and return its JSON-decoded result."""
        qid = next(self._ids)
        answer = queue.Queue()
        self._pending[qid] = answer
        js = " ".join(js_expression.split())  # must be a single console line
        if not self.send(f'js "@@DASH:{qid}:" + JSON.stringify({js})'):
            self._pending.pop(qid, None)
            raise RuntimeError("server is not running")
        try:
            return json.loads(answer.get(timeout=timeout))
        except queue.Empty:
            self._pending.pop(qid, None)
            raise RuntimeError("server did not answer (still starting?)") from None

    def hosting(self):
        return bool(self.query("!Vars.state.isMenu()"))


server = MindustryServer()
