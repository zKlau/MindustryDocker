"""Saved games (files in config/saves)."""

from .. import settings
from ..server import server
from ..validation import is_msav, slot


def list_all():
    if not settings.SAVES_DIR.exists():
        return []
    files = sorted(settings.SAVES_DIR.glob("*.msav"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "name": f.stem,
            "size": f.stat().st_size,
            "mtime": int(f.stat().st_mtime),
            "auto": f.stem == settings.SESSION_SAVE or f.stem.startswith("auto_"),
        }
        for f in files
    ]


def path(name):
    return settings.SAVES_DIR / f"{slot(name)}.msav"


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
    settings.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    path(stem).write_bytes(data)
