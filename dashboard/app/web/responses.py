import json

from .constants import BINARY_TYPE, IMAGE_CACHE, PNG_TYPE
from .router import Response

OK_BODY = json.dumps({"ok": True}).encode()


def ok(headers=None):
    return Response(OK_BODY, headers=headers)


def png(image):
    return Response(image, content_type=PNG_TYPE, headers={"Cache-Control": IMAGE_CACHE})


def download(path):
    return Response(
        path.read_bytes(),
        content_type=BINARY_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )
