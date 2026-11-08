import re

_COLOR_TAG = re.compile(r"\[[^\[\]]*\]")


def strip_colors(text):
    return _COLOR_TAG.sub("", str(text or "")).strip()


def first_line(text):
    lines = strip_colors(text).splitlines() or [""]

    return lines[0].strip()


def slugify(text, separator, max_length, fallback):
    slug = re.sub(r"[^A-Za-z0-9_-]+", separator, str(text)).strip(separator)[:max_length]

    return slug or fallback


def on_off(flag):
    if flag:
        return "on"

    return "off"
