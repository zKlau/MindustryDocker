import signal
import sys
from http.server import ThreadingHTTPServer

from . import settings
from .common.log import log
from .common.threads import run_in_background
from .server import server
from .services import startup
from .services.access import hooks as access_hooks
from .services.maps import previews
from .services.stats import chat as stats_chat
from .services.stats import collector as stats_collector

LISTEN_ADDRESS = "0.0.0.0"


def forward_stdin():
    try:
        for line in sys.stdin:
            server.send(line)
    except (OSError, ValueError):
        pass


def start_dashboard():
    from .web.handler import Handler

    httpd = ThreadingHTTPServer((LISTEN_ADDRESS, settings.HTTP_PORT), Handler)
    httpd.daemon_threads = True
    run_in_background(httpd.serve_forever)
    log(f"web dashboard listening on port {settings.HTTP_PORT}")


def register_hooks():
    server.on_ready.extend(
        [
            startup.on_server_ready,
            previews.apply_block_colors,
            access_hooks.on_server_ready,
            stats_collector.on_server_ready,
        ]
    )
    server.line_filters.extend([access_hooks.filter_line, stats_chat.filter_line])


def main():
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def stop(*_):
        log("shutting down: saving the world first")
        server.shutdown(save_name=settings.SESSION_SAVE)
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    if sys.stdin and not sys.stdin.closed:
        run_in_background(forward_stdin)

    if settings.ADMIN_PASSWORD:
        start_dashboard()
    else:
        log("ADMIN_PASSWORD is not set - web dashboard disabled")

    register_hooks()
    run_in_background(stats_collector.run_collector)
    sys.exit(server.run_forever(startup.start_commands))


if __name__ == "__main__":
    main()
