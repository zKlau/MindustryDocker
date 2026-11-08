from ...common.constants import DEFAULT_GAMEMODE, KIND_MAP
from ...services.maps import catalog, files, hosting, online, previews
from .. import responses
from ..constants import UPLOAD_LIMIT
from ..router import get, post


@get("/api/maps")
def list_maps(req):
    return catalog.list_all()


@post("/api/maps/host")
def host_map(req):
    hosting.host(req.field("kind", KIND_MAP), req.field("name"), req.field("mode", DEFAULT_GAMEMODE))


@post("/api/maps/next")
def next_map(req):
    hosting.set_next(req.field("name"))


@post("/api/maps/upload")
def upload_map(req):
    files.upload(req.arg("name"), req.body(UPLOAD_LIMIT))


@post("/api/maps/delete")
def delete_map(req):
    files.delete_custom(req.field("name"))


@get("/api/maps/preview")
def map_preview(req):
    return responses.png(previews.get(req.arg("kind", KIND_MAP), req.arg("name")))


@get("/api/online/maps")
def search_online_maps(req):
    return online.search(req.arg("q"), req.arg("sort", online.DEFAULT_SORT), req.int_arg("page"))


@get("/api/online/maps/details")
def online_map_details(req):
    return online.details(req.arg("id"))


@get("/api/online/maps/preview")
def online_map_preview(req):
    return responses.png(online.preview(req.arg("id")))


@post("/api/online/maps/install")
def install_online_map(req):
    map_id = req.field("id")
    if req.field("play", False):
        name = online.install_and_play(map_id, req.field("mode", DEFAULT_GAMEMODE))
    else:
        name = online.install(map_id)

    return {"name": name}
