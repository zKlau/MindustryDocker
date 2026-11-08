import json
import pathlib
import sys
import urllib.request

IMG = pathlib.Path(__file__).resolve().parent.parent / "dashboard" / "static" / "img"
SPRITES = "https://raw.githubusercontent.com/Anuken/Mindustry/{ref}/core/assets-raw/sprites/"
ITEM_LISTING = (
    "https://api.github.com/repos/Anuken/Mindustry/contents/core/assets-raw/sprites/items?ref={ref}"
)
ITEM_PREFIX = "item-"
POWER_ICONS = ("battery", "combustion-generator", "power-node", "diode")


def fetch(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def fetch_items(ref):
    output = IMG / "items"
    output.mkdir(parents=True, exist_ok=True)
    entries = json.loads(fetch(ITEM_LISTING.format(ref=ref)))
    icons = [e for e in entries if e["name"].startswith(ITEM_PREFIX) and e["name"].endswith(".png")]
    for entry in icons:
        (output / entry["name"].removeprefix(ITEM_PREFIX)).write_bytes(fetch(entry["download_url"]))
    print(f"wrote {len(icons)} item icons to {output}")


def fetch_power(ref):
    output = IMG / "power"
    output.mkdir(parents=True, exist_ok=True)
    for name in POWER_ICONS:
        (output / f"{name}.png").write_bytes(fetch(f"{SPRITES.format(ref=ref)}blocks/power/{name}.png"))
    print(f"wrote {len(POWER_ICONS)} power icons to {output}")


def main(ref):
    fetch_items(ref)
    fetch_power(ref)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "master")
