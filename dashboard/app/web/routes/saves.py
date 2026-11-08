from ...services import saves
from .. import responses
from ..constants import UPLOAD_LIMIT
from ..router import ApiError, get, post


@get("/api/saves")
def list_saves(req):
    return saves.list_all()


@post("/api/saves/save")
def save_game(req):
    saves.save(req.field("name"))


@post("/api/saves/load")
def load_save(req):
    saves.load(req.field("name"))


@post("/api/saves/delete")
def delete_save(req):
    saves.delete(req.field("name"))


@post("/api/saves/upload")
def upload_save(req):
    saves.upload(req.arg("name"), req.body(UPLOAD_LIMIT))


@get("/api/saves/download")
def download_save(req):
    path = saves.path(req.arg("name"))
    if not path.exists():
        raise ApiError(404, "Save not found")

    return responses.download(path)
