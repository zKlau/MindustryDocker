import json
import pathlib
import sys
import urllib.request

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "dashboard" / "static" / "img" / "items"
LISTING = "https://api.github.com/repos/Anuken/Mindustry/contents/core/assets-raw/sprites/items?ref={ref}"
PREFIX = "item-"


def fetch(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def main(ref):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries = json.loads(fetch(LISTING.format(ref=ref)))
    icons = [e for e in entries if e["name"].startswith(PREFIX) and e["name"].endswith(".png")]
    for entry in icons:
        (OUTPUT / entry["name"].removeprefix(PREFIX)).write_bytes(fetch(entry["download_url"]))
    print(f"wrote {len(icons)} item icons to {OUTPUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "master")
