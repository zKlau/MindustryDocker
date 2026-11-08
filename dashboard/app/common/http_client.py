import json
import urllib.error
import urllib.parse
import urllib.request

from .constants import KB, MB

urlencode = urllib.parse.urlencode

USER_AGENT = "MindustryDockerDashboard/1.0 (+https://github.com/zKlau/MindustryDocker)"
DEFAULT_LIMIT = 100 * MB
JSON_LIMIT = 20 * MB
DEFAULT_TIMEOUT = 30
CHUNK = 64 * KB


class HttpStatusError(RuntimeError):
    def __init__(self, url, status):
        super().__init__(f"{_host(url)} answered with HTTP {status}")
        self.status = status


def _host(url):
    return urllib.parse.urlparse(url).netloc


def fetch(url, headers=None, limit=DEFAULT_LIMIT, timeout=DEFAULT_TIMEOUT):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _read_limited(response, limit)
    except urllib.error.HTTPError as error:
        raise HttpStatusError(url, error.code) from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"Could not reach {_host(url)}: {error}") from None


def fetch_json(url, headers=None, timeout=DEFAULT_TIMEOUT):
    return json.loads(fetch(url, headers=headers, limit=JSON_LIMIT, timeout=timeout))


def _read_limited(response, limit):
    body = bytearray()
    while True:
        chunk = response.read(CHUNK)
        if not chunk:
            return bytes(body)
        body += chunk
        if len(body) > limit:
            raise RuntimeError("Download is too large")
