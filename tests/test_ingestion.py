import pytest

from app.config import settings
from app.ingestion.loader import (
    FileRejectedError,
    PathNotAllowedError,
    TooManyFilesError,
    filter_files,
    load_directory,
    read_file,
    resolve_within_root,
)
from app.schemas.ingestion import ProjectFile


def skipped_reasons(result):
    return {item.path: item.reason for item in result.skipped}


def test_filter_files_skips_junk_directories():
    files = [
        ProjectFile(path="src/app.py", content="print('hi')"),
        ProjectFile(path="node_modules/lib/index.js", content="x"),
        ProjectFile(path="project/.git/config", content="x"),
    ]

    result = filter_files(files)

    assert [f.path for f in result.accepted] == ["src/app.py"]
    reasons = skipped_reasons(result)
    assert "node_modules" in reasons["node_modules/lib/index.js"]
    assert ".git" in reasons["project/.git/config"]


def test_filter_files_skips_binary_and_oversized(monkeypatch):
    monkeypatch.setattr(settings, "max_file_bytes", 10)
    files = [
        ProjectFile(path="image.bin", content="ab\0cd"),
        ProjectFile(path="big.txt", content="x" * 11),
        ProjectFile(path="ok.txt", content="fine"),
    ]

    result = filter_files(files)

    assert [f.path for f in result.accepted] == ["ok.txt"]
    reasons = skipped_reasons(result)
    assert reasons["image.bin"] == "binary file"
    assert "larger than" in reasons["big.txt"]


def test_filter_files_rejects_too_many(monkeypatch):
    monkeypatch.setattr(settings, "max_files", 1)
    files = [ProjectFile(path="a.py", content=""), ProjectFile(path="b.py", content="")]

    with pytest.raises(TooManyFilesError):
        filter_files(files)


def test_load_directory_reads_text_and_skips_the_rest(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\0\0")
    (tmp_path / "latin1.txt").write_bytes("caf\xe9".encode("latin-1"))
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("x")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "util.py").write_text("y = 1")

    result = load_directory(tmp_path)

    assert sorted(f.path for f in result.accepted) == ["main.py", "pkg/util.py"]
    reasons = skipped_reasons(result)
    assert reasons["logo.png"] == "binary file"
    assert reasons["latin1.txt"] == "not UTF-8 text"
    assert reasons["node_modules"] == "skipped directory"
    assert "node_modules/dep.js" not in reasons


def test_load_directory_skips_symlinks(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    project = tmp_path / "project"
    project.mkdir()
    (project / "real.py").write_text("x = 1")
    (project / "link.txt").symlink_to(outside / "secret.txt")
    (project / "linked_dir").symlink_to(outside, target_is_directory=True)

    result = load_directory(project)

    assert [f.path for f in result.accepted] == ["real.py"]
    reasons = skipped_reasons(result)
    assert reasons["link.txt"] == "symlink"
    assert reasons["linked_dir"] == "symlink"


def test_resolve_within_root_allows_paths_inside(tmp_path):
    (tmp_path / "repo").mkdir()

    assert resolve_within_root(str(tmp_path), "repo") == (tmp_path / "repo").resolve()
    assert resolve_within_root(str(tmp_path), "") == tmp_path.resolve()


def test_read_file_returns_content_for_an_accepted_file(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "util.py").write_text("y = 1")

    result = read_file(tmp_path, "pkg/util.py")

    assert result == ProjectFile(path="pkg/util.py", content="y = 1")


def test_read_file_rejects_oversized_or_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "max_file_bytes", 2)
    (tmp_path / "big.txt").write_text("too long")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\0\0")

    with pytest.raises(FileRejectedError):
        read_file(tmp_path, "big.txt")
    with pytest.raises(FileRejectedError):
        read_file(tmp_path, "logo.png")


def test_read_file_missing_or_escaping_path_not_found(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    root = tmp_path / "root"
    root.mkdir()

    with pytest.raises(FileNotFoundError):
        read_file(root, "missing.py")
    with pytest.raises(PathNotAllowedError):
        read_file(root, "../outside/secret.txt")


def test_resolve_within_root_rejects_escapes(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "sneaky").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathNotAllowedError):
        resolve_within_root(str(root), "../outside")
    with pytest.raises(PathNotAllowedError):
        resolve_within_root(str(root), str(outside))
    with pytest.raises(PathNotAllowedError):
        resolve_within_root(str(root), "sneaky")
