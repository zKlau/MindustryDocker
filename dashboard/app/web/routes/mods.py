from ...services.mods import catalog, installed, online
from ..constants import UPLOAD_LIMIT
from ..router import get, post


@get("/api/mods")
def list_mods(req):
    return installed.list_all()


@post("/api/mods/upload")
def upload_mod(req):
    installed.upload(req.arg("name"), req.body(UPLOAD_LIMIT))


@post("/api/mods/delete")
def delete_mod(req):
    installed.delete(req.field("file"))


@get("/api/online/mods")
def search_online_mods(req):
    only_compatible = req.arg("compatible", "1") != "0"

    return online.search(
        req.arg("q"), req.arg("sort", catalog.DEFAULT_SORT), req.int_arg("page"), only_compatible
    )


@post("/api/online/mods/install")
def install_online_mod(req):
    return online.install(req.field("repo"))
