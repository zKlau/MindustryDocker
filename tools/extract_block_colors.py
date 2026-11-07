"""Build dashboard/app/data/block_colors.json from Mindustry's raw environment sprites.

The headless server never loads textures, so every block's map colour is black and
map previews come out empty. This script computes the colour once from the sprites:

    git clone --depth 1 --filter=blob:none --sparse --branch v160.7 \
        https://github.com/Anuken/Mindustry.git mindustry-src
    git -C mindustry-src sparse-checkout set core/assets-raw/sprites/blocks/environment
    python tools/extract_block_colors.py mindustry-src/core/assets-raw/sprites/blocks/environment

Standard library only (includes a minimal PNG decoder).
"""

import json
import pathlib
import re
import struct
import sys
import zlib

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "dashboard" / "app" / "data" / "block_colors.json"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def read_chunks(data):
    position = 8
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position : position + 8])
        yield kind, data[position + 8 : position + 8 + length]
        position += 12 + length


def unfilter(raw, width, height, bytes_per_pixel):
    stride = width * bytes_per_pixel
    rows = []
    previous = bytearray(stride)
    position = 0
    for _ in range(height):
        filter_type = raw[position]
        row = bytearray(raw[position + 1 : position + 1 + stride])
        position += 1 + stride
        for i in range(stride):
            left = 0
            up_left = 0
            if i >= bytes_per_pixel:
                left = row[i - bytes_per_pixel]
                up_left = previous[i - bytes_per_pixel]
            up = previous[i]
            if filter_type == 1:
                row[i] = (row[i] + left) & 0xFF
            elif filter_type == 2:
                row[i] = (row[i] + up) & 0xFF
            elif filter_type == 3:
                row[i] = (row[i] + (left + up) // 2) & 0xFF
            elif filter_type == 4:
                estimate = left + up - up_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - up_left))
                predictor = (left, up, up_left)[distances.index(min(distances))]
                row[i] = (row[i] + predictor) & 0xFF
        rows.append(row)
        previous = row
    return rows


def read_png(path):
    """Return (header, palette, transparency, decompressed pixel data)."""
    header = None
    palette = b""
    transparency = b""
    compressed = bytearray()
    for kind, body in read_chunks(path.read_bytes()):
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"tRNS":
            transparency = body
        elif kind == b"IDAT":
            compressed += body
    return header, palette, transparency, zlib.decompress(bytes(compressed))


def to_rgba(color_type, pixel, palette, transparency):
    if color_type == 6:
        return tuple(pixel)
    if color_type == 2:
        return (pixel[0], pixel[1], pixel[2], 255)
    if color_type == 0:
        return (pixel[0], pixel[0], pixel[0], 255)
    if color_type == 4:
        return (pixel[0], pixel[0], pixel[0], pixel[1])
    index = pixel[0]
    alpha = 255
    if index < len(transparency):
        alpha = transparency[index]
    return (*palette[index * 3 : index * 3 + 3], alpha)


def pixels(path):
    """Yield (r, g, b, a) for every pixel of an 8-bit, non-interlaced PNG."""
    header, palette, transparency, raw = read_png(path)
    width, height, bit_depth, color_type, _, _, interlace = header
    if bit_depth != 8 or interlace or color_type not in CHANNELS:
        return
    channels = CHANNELS[color_type]
    for row in unfilter(raw, width, height, channels):
        for x in range(width):
            yield to_rgba(color_type, row[x * channels : (x + 1) * channels], palette, transparency)


def average_color(path):
    total = [0, 0, 0]
    count = 0
    for r, g, b, a in pixels(path):
        if a < 128:
            continue
        total[0] += r
        total[1] += g
        total[2] += b
        count += 1
    if count == 0:
        return None
    return "".join(f"{round(c / count):02x}" for c in total)


# Blocks without their own environment sprite (props, boulders, overlays): borrow a similar colour.
BORROWED = {
    "boulder": "stone",
    "sand-boulder": "sand-floor",
    "snow-boulder": "snow",
    "shale-boulder": "shale",
    "dacite-boulder": "dacite",
    "basalt-boulder": "basalt",
    "carbon-boulder": "carbon-stone",
    "ferric-boulder": "ferric-stone",
    "beryllic-boulder": "beryllic-stone",
    "yellow-stone-boulder": "yellow-stone",
    "arkyic-boulder": "arkyic-stone",
    "crystalline-boulder": "crystalline-stone",
    "red-ice-boulder": "red-ice",
    "rhyolite-boulder": "rhyolite",
    "red-stone-boulder": "red-stone",
    "metal-floor-damaged": "metal-floor",
    "character-overlay": "metal-floor",
    "character-overlay-white": "metal-floor",
    "rune-overlay": "metal-floor",
    "rune-overlay-crux": "metal-floor",
}
BORROWED.update({f"dark-panel-{i}": "dark-panel-1" for i in range(2, 7)})
BORROWED.update({f"metal-tiles-{i}": "metal-tiles-1" for i in range(2, 14)})
FIXED = {"spore-cluster": "7457ce", "redweed": "a8433c", "pur-bush": "9e64c6"}


def block_names(path):
    """stone1.png -> stone (variant sprites), metal-floor-2.png -> metal-floor-2 (exact name)."""
    stem = path.stem
    if stem.endswith("-large") or "-edge" in stem or stem.endswith("-shadow"):
        return []
    names = [stem]
    if re.search(r"[a-z]\d+$", stem):
        names.append(re.sub(r"\d+$", "", stem))
    return names


def main(sprite_dir):
    colors = {}
    for path in sorted(pathlib.Path(sprite_dir).glob("*.png")):
        names = [n for n in block_names(path) if n not in colors]
        if not names:
            continue
        color = average_color(path)
        if color:
            for name in names:
                colors[name] = color
    for name, source in BORROWED.items():
        if name not in colors and source in colors:
            colors[name] = colors[source]
    for name, color in FIXED.items():
        colors.setdefault(name, color)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(colors, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(colors)} colours to {OUTPUT}")


if __name__ == "__main__":
    main(sys.argv[1])
