import json


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def write_json_atomic(path, data, indent=None, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    separators = None
    if indent is None:
        separators = (",", ":")
    tmp.write_text(json.dumps(data, indent=indent, separators=separators))
    if private:
        tmp.chmod(0o600)
    tmp.replace(path)


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
