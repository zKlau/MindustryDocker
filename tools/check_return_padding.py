import ast
import pathlib
import sys

BLOCK_FIELDS = ("body", "orelse", "finalbody", "handlers", "cases")


def _blocks(tree):
    for node in ast.walk(tree):
        for field in BLOCK_FIELDS:
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                yield block


def _has_blank_line(lines, start, end):
    return any(not lines[index].strip() for index in range(start, end - 1))


def _is_docstring(statement):
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _needs_padding(lines, previous, statement):
    if not isinstance(statement, ast.Return) or _is_docstring(previous):
        return False

    return not _has_blank_line(lines, previous.end_lineno, statement.lineno)


def missing_padding(source):
    tree = ast.parse(source)
    lines = source.splitlines()
    problems = set()
    for block in _blocks(tree):
        for previous, statement in zip(block, block[1:], strict=False):
            if _needs_padding(lines, previous, statement):
                problems.add(previous.end_lineno)

    return sorted(problems)


def fix(source, after_lines):
    lines = source.splitlines(keepends=True)
    for line_number in reversed(after_lines):
        lines.insert(line_number, "\n")

    return "".join(lines)


def python_files(paths):
    for path in map(pathlib.Path, paths):
        if path.is_dir():
            yield from sorted(path.rglob("*.py"))
        else:
            yield path


def main(argv):
    apply_fix = "--fix" in argv
    paths = [arg for arg in argv if arg != "--fix"] or ["."]
    failures = 0
    for path in python_files(paths):
        source = path.read_text(encoding="utf-8")
        problems = missing_padding(source)
        if not problems:
            continue
        if apply_fix:
            path.write_text(fix(source, problems), encoding="utf-8", newline="\n")
            continue
        failures += len(problems)
        for line_number in problems:
            print(f"{path}:{line_number + 1}: expected an empty line before `return`")

    if failures:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
