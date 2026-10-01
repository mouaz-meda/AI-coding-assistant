import re

from app.ai.llm import strip_code_fence
from app.review.diff import make_diff
from app.schemas.review import FileEdit

FILE_MARKER_RE = re.compile(r"^=== (.+) ===$", re.MULTILINE)


def parse_file_edits(text: str, originals: dict[str, str]) -> list[FileEdit]:
    """Split a multi-file fix reply on '=== path ===' markers into per-file diffs.

    Unknown paths (the model referencing a file it wasn't given) and files whose
    content didn't actually change are silently skipped rather than erroring —
    the model's marker format isn't guaranteed, so this stays defensive.
    """
    parts = FILE_MARKER_RE.split(strip_code_fence(text))
    edits = []
    for path, content in zip(parts[1::2], parts[2::2]):
        path = path.strip()
        original = originals.get(path)
        if original is None:
            continue
        content = content.strip("\n")
        if content == original.rstrip("\n"):
            continue
        edits.append(FileEdit(path=path, output=content, diff=make_diff(path, original, content)))
    return edits
