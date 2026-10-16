from app.ai.chunking import chunk_file
from app.schemas.ingestion import ProjectFile


# .txt is used for these generic-splitter tests deliberately — .py/.js/.ts now
# route through the language-aware splitter (see the dedicated tests below),
# so a non-code extension is what actually exercises the line-based fallback.


def test_chunk_file_returns_single_chunk_when_shorter_than_chunk_size():
    file = ProjectFile(path="a.txt", content="\n".join(f"line{i}" for i in range(10)))

    chunks = chunk_file(file, chunk_lines=40, overlap=5)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 10
    assert chunks[0].text == file.content


def test_chunk_file_splits_with_overlap():
    file = ProjectFile(path="a.txt", content="\n".join(f"line{i}" for i in range(25)))

    chunks = chunk_file(file, chunk_lines=10, overlap=2)

    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 10), (9, 18), (17, 25)]
    # Overlapping lines actually appear in both neighboring chunks.
    assert "line8" in chunks[0].text
    assert "line8" in chunks[1].text


def test_chunk_file_handles_empty_content():
    file = ProjectFile(path="empty.txt", content="")

    chunks = chunk_file(file)

    assert len(chunks) == 1
    assert chunks[0].text == ""


def test_chunk_file_caps_chunk_length_even_with_few_long_lines():
    # A handful of very long lines (minified code, a long data literal) must
    # not produce a chunk that blows past an embedding model's token limit.
    file = ProjectFile(path="minified.txt", content="x" * 100_000)

    chunks = chunk_file(file, chunk_lines=40, overlap=5, max_chars=4000)

    assert all(len(c.text) <= 4000 for c in chunks)


def test_chunk_file_snaps_end_to_nearby_blank_line():
    # Blank line at index 3 falls inside the overlap search window for the
    # first chunk's natural cut point (index 5) — the chunk should end right
    # after it instead of continuing into the next block.
    lines = ["a", "b", "c", "", "d", "e", "f", "g", "h", "i"]
    file = ProjectFile(path="a.txt", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    assert chunks[0].end_line == 4
    assert chunks[0].text == "a\nb\nc\n"


def test_chunk_file_snapping_never_skips_a_line():
    # Even with snapping shortening some chunks, every line must still appear
    # in at least one chunk — a coverage gap would mean that content can
    # never be found by retrieval at all.
    lines = ["a", "b", "c", "", "d", "e", "f", "g", "h", "i"]
    file = ProjectFile(path="a.txt", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    covered = set()
    for c in chunks:
        covered.update(range(c.start_line, c.end_line + 1))
    assert covered == set(range(1, len(lines) + 1))


def test_chunk_file_falls_back_to_hard_cut_when_no_blank_line_nearby():
    lines = [f"line{i}" for i in range(10)]  # no blank lines at all
    file = ProjectFile(path="a.txt", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    # Unchanged from the pre-snapping behavior: hard cut at chunk_lines.
    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 5), (4, 8), (7, 10)]


def test_chunk_file_falls_back_to_lines_for_unsupported_language():
    # An extension the code splitter doesn't know (e.g. Go) should behave
    # exactly like the generic .txt case above, not error out.
    lines = [f"line{i}" for i in range(10)]
    file = ProjectFile(path="a.go", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 5), (4, 8), (7, 10)]


def _python_source(n_functions: int) -> str:
    return "\n\n".join(f"def func_{i}(a, b):\n    return a + b" for i in range(n_functions))


def test_chunk_file_splits_python_at_function_boundaries(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rag_code_chunk_overlap_chars", 0)
    file = ProjectFile(path="math_utils.py", content=_python_source(3))

    chunks = chunk_file(file, max_chars=40)

    assert len(chunks) > 1
    # Reconstructed line ranges must actually point back at the right text.
    lines = file.content.splitlines()
    for chunk in chunks:
        assert chunk.text.strip() in "\n".join(lines[chunk.start_line - 1 : chunk.end_line])


def test_chunk_file_splits_javascript_at_function_boundaries(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rag_code_chunk_overlap_chars", 0)
    code = "\n\n".join(f"function fn{i}() {{\n  return {i};\n}}" for i in range(3))
    file = ProjectFile(path="utils.js", content=code)

    chunks = chunk_file(file, max_chars=40)

    assert len(chunks) > 1
    assert all(c.text.strip() for c in chunks)


def test_chunk_file_splits_typescript_at_function_boundaries(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rag_code_chunk_overlap_chars", 0)
    code = "\n\n".join(f"function fn{i}(): number {{\n  return {i};\n}}" for i in range(3))
    file = ProjectFile(path="utils.ts", content=code)

    chunks = chunk_file(file, max_chars=40)

    assert len(chunks) > 1
    assert all(c.text.strip() for c in chunks)


def test_chunk_file_handles_empty_python_file():
    file = ProjectFile(path="empty.py", content="")

    chunks = chunk_file(file)

    assert len(chunks) == 1
    assert chunks[0].text == ""
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 1
