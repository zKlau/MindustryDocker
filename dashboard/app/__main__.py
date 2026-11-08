"""Entry point: `python -m app`.

Starts the web dashboard (if ADMIN_PASSWORD is set) and supervises the Mindustry server.
"""

import signal
import sys
import threading
from http.server import ThreadingHTTPServer

from . import settings
from .server import log, server
from .services import access, previews, startup, stats


def forward_stdin():
    """Keep `docker attach` working: lines typed into the container go to the server console."""
    try:
        for line in sys.stdin:
            server.send(line)
    except (OSError, ValueError):
        pass


def start_dashboard():
    from .web.handler import Handler

    httpd = ThreadingHTTPServer(("0.0.0.0", settings.HTTP_PORT), Handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    log(f"web dashboard listening on port {settings.HTTP_PORT}")


def main():
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def stop(*_):
        log("shutting down: saving the world first")
        server.shutdown(save_name=settings.SESSION_SAVE)
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    if sys.stdin and not sys.stdin.closed:
        threading.Thread(target=forward_stdin, daemon=True).start()

    if settings.ADMIN_PASSWORD:
        start_dashboard()
    else:
        log("ADMIN_PASSWORD is not set - web dashboard disabled")

    server.on_ready.append(startup.on_server_ready)
    server.on_ready.append(previews.apply_block_colors)
    server.on_ready.append(access.on_server_ready)
    server.line_filters.append(access.filter_line)
    server.on_ready.append(stats.on_server_ready)
    server.line_filters.append(stats.filter_line)
    threading.Thread(target=stats.run_collector, daemon=True).start()
    sys.exit(server.run_forever(startup.start_commands))


if __name__ == "__main__":
    main()
