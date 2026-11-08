from ..common.constants import KB, MB

API_PREFIX = "/api/"
HEALTH_PATH = "/healthz"
INDEX_FILE = "index.html"

CSRF_HEADER = "X-Dashboard"
CSRF_VALUE = "1"

JSON_TYPE = "application/json"
PNG_TYPE = "image/png"
BINARY_TYPE = "application/octet-stream"

JSON_BODY_LIMIT = 64 * KB
UPLOAD_LIMIT = 100 * MB

NO_STORE = "no-store"
STATIC_CACHE = "public, max-age=300"
IMAGE_CACHE = "private, max-age=86400"

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:"
    ),
}
