import json
import re


def literal(value):
    return json.dumps(value)


def fill(template, **parts):
    if not parts:
        return template
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, parts)) + r")\b")

    return pattern.sub(lambda match: str(parts[match.group(1)]), template)
