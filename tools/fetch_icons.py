import json
import pathlib
import sys
import urllib.request

IMG = pathlib.Path(__file__).resolve().parent.parent / "dashboard" / "static" / "img"
SPRITES = "https://raw.githubusercontent.com/Anuken/Mindustry/{ref}/core/assets-raw/sprites/"
ITEM_LISTING = (
    "https://api.github.com/repos/Anuken/Mindustry/contents/core/assets-raw/sprites/items?ref={ref}"
)
LISTED_ICONS = {"item-": "items", "liquid-": "liquids"}
POWER_ICONS = ("battery", "combustion-generator", "power-node", "diode")


def fetch(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def fetch_listed(ref):
    entries = json.loads(fetch(ITEM_LISTING.format(ref=ref)))
    for prefix, folder in LISTED_ICONS.items():
        output = IMG / folder
        output.mkdir(parents=True, exist_ok=True)
        icons = [e for e in entries if e["name"].startswith(prefix) and e["name"].endswith(".png")]
        for entry in icons:
            (output / entry["name"].removeprefix(prefix)).write_bytes(fetch(entry["download_url"]))
        print(f"wrote {len(icons)} icons to {output}")


def fetch_power(ref):
    output = IMG / "power"
    output.mkdir(parents=True, exist_ok=True)
    for name in POWER_ICONS:
        (output / f"{name}.png").write_bytes(fetch(f"{SPRITES.format(ref=ref)}blocks/power/{name}.png"))
    print(f"wrote {len(POWER_ICONS)} power icons to {output}")


def main(ref):
    fetch_listed(ref)
    fetch_power(ref)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "master")
