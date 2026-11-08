from .. import settings
from ..common.constants import MSAV_EXTENSION
from ..common.files import write_bytes
from ..common.validation import is_msav, slot
from ..server import server

AUTOSAVE_PREFIX = "auto_"


def _describe(file):
    stat = file.stat()

    return {
        "name": file.stem,
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "auto": file.stem == settings.SESSION_SAVE or file.stem.startswith(AUTOSAVE_PREFIX),
    }


def list_all():
    if not settings.SAVES_DIR.exists():
        return []
    files = settings.SAVES_DIR.glob(f"*{MSAV_EXTENSION}")

    return [_describe(f) for f in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)]


def path(name):
    return settings.SAVES_DIR / f"{slot(name)}{MSAV_EXTENSION}"


def save(name):
    if not server.hosting():
        raise ValueError("No game is running")
    server.send(f"save {slot(name)}")


def load(name):
    if not path(name).exists():
        raise ValueError("Save not found")
    if server.hosting():
        server.send("stop")
    server.send(f"load {slot(name)}")


def delete(name):
    path(name).unlink(missing_ok=True)


def upload(file_name, data):
    stem = file_name.rsplit(".", 1)[0].replace(" ", "_")
    if not is_msav(data):
        raise ValueError("Not a Mindustry save file")
    write_bytes(path(stem), data)
