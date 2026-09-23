import difflib


def make_diff(path: str, original: str, fixed: str) -> str:
    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(diff_lines)
