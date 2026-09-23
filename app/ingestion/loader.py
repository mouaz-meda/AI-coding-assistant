import os
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.schemas.ingestion import ProjectFile, SkippedFile

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".next", "dist", "build"}


class TooManyFilesError(Exception):
    pass


class PathNotAllowedError(Exception):
    pass


@dataclass
class IngestResult:
    accepted: list[ProjectFile] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)


def check_file(path: str, data: bytes) -> str | None:
    """Return the reason a file must be skipped, or None if it is usable text."""
    for part in path.replace("\\", "/").split("/")[:-1]:
        if part in SKIP_DIRS:
            return f"inside skipped directory '{part}'"
    if len(data) > settings.max_file_bytes:
        return f"larger than {settings.max_file_bytes} bytes"
    if b"\0" in data:
        return "binary file"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return "not UTF-8 text"
    return None


def filter_files(files: list[ProjectFile]) -> IngestResult:
    if len(files) > settings.max_files:
        raise TooManyFilesError(f"Too many files (limit is {settings.max_files})")

    result = IngestResult()
    for file in files:
        try:
            data = file.content.encode("utf-8")
        except UnicodeEncodeError:
            result.skipped.append(SkippedFile(path=file.path, reason="not UTF-8 text"))
            continue

        reason = check_file(file.path, data)
        if reason:
            result.skipped.append(SkippedFile(path=file.path, reason=reason))
        else:
            result.accepted.append(file)
    return result


def load_directory(root: Path) -> IngestResult:
    result = IngestResult()
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)

        kept_dirs = []
        for name in dirnames:
            relative = (current / name).relative_to(root).as_posix()
            if name in SKIP_DIRS:
                result.skipped.append(SkippedFile(path=relative, reason="skipped directory"))
            elif (current / name).is_symlink():
                result.skipped.append(SkippedFile(path=relative, reason="symlink"))
            else:
                kept_dirs.append(name)
        dirnames[:] = kept_dirs

        for name in filenames:
            full_path = current / name
            relative = full_path.relative_to(root).as_posix()

            if full_path.is_symlink():
                result.skipped.append(SkippedFile(path=relative, reason="symlink"))
                continue

            try:
                with open(full_path, "rb") as f:
                    data = f.read(settings.max_file_bytes + 1)
            except OSError:
                result.skipped.append(SkippedFile(path=relative, reason="unreadable"))
                continue

            reason = check_file(relative, data)
            if reason:
                result.skipped.append(SkippedFile(path=relative, reason=reason))
                continue

            if len(result.accepted) >= settings.max_files:
                raise TooManyFilesError(f"Too many files (limit is {settings.max_files})")
            result.accepted.append(ProjectFile(path=relative, content=data.decode("utf-8")))
    return result


def resolve_within_root(root: str, user_path: str) -> Path:
    root_path = Path(root).resolve()
    target = (root_path / user_path).resolve()
    if not target.is_relative_to(root_path):
        raise PathNotAllowedError("Path is outside the allowed ingest root")
    return target
