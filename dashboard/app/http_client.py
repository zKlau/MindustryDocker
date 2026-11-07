"""Outgoing HTTP requests (MindustryTool, GitHub) with size limits and readable errors."""

import json
import urllib.error
import urllib.parse
import urllib.request

urlencode = urllib.parse.urlencode

USER_AGENT = "MindustryDockerDashboard/1.0 (+https://github.com/zKlau/MindustryDocker)"
DEFAULT_LIMIT = 100 * 1024 * 1024
CHUNK = 64 * 1024


class HttpStatusError(RuntimeError):
    def __init__(self, url, status):
        host = urllib.parse.urlparse(url).netloc
        super().__init__(f"{host} answered with HTTP {status}")
        self.status = status


def fetch(url, headers=None, limit=DEFAULT_LIMIT, timeout=30):
    """GET a URL and return the body as bytes. Raises RuntimeError on network problems."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _read_limited(response, limit)
    except urllib.error.HTTPError as error:
        raise HttpStatusError(url, error.code) from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        host = urllib.parse.urlparse(url).netloc
        raise RuntimeError(f"Could not reach {host}: {error}") from None


def fetch_json(url, headers=None, timeout=30):
    return json.loads(fetch(url, headers=headers, limit=20 * 1024 * 1024, timeout=timeout))


def _read_limited(response, limit):
    body = bytearray()
    while True:
        chunk = response.read(CHUNK)
        if not chunk:
            return bytes(body)
        body += chunk
        if len(body) > limit:
            raise RuntimeError("Download is too large")
