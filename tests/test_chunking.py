from app.ai.chunking import chunk_file
from app.config import settings
from app.schemas.ingestion import ProjectFile


# .txt is used for these generic-splitter tests deliberately — .py/.js/.ts route
# through the language-aware splitter (see the dedicated tests below), so a
# non-code extension is what actually exercises the plain character splitter.


def test_chunk_file_returns_single_chunk_when_shorter_than_chunk_size():
    file = ProjectFile(path="a.txt", content="\n".join(f"line{i}" for i in range(10)))

    chunks = chunk_file(file, max_chars=4000)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 10
    assert chunks[0].text == file.content


def test_chunk_file_splits_long_content_with_overlap(monkeypatch):
    monkeypatch.setattr(settings, "rag_chunk_overlap_chars", 10)
    lines = [f"line{i} filler text to pad the line out a bit" for i in range(30)]
    file = ProjectFile(path="a.txt", content="\n".join(lines))

    chunks = chunk_file(file, max_chars=200)

    assert len(chunks) > 1
    # Reconstructed line ranges must actually point back at the right text.
    all_lines = file.content.splitlines()
    for chunk in chunks:
        assert chunk.text.strip() in "\n".join(all_lines[chunk.start_line - 1 : chunk.end_line])
    # Coverage: every line shows up in at least one chunk — a gap would mean
    # that content can never be found by retrieval at all.
    covered = set()
    for chunk in chunks:
        covered.update(range(chunk.start_line, chunk.end_line + 1))
    assert covered == set(range(1, len(lines) + 1))


def test_chunk_file_caps_chunk_length_even_with_few_long_lines():
    # A handful of very long lines (minified code, a long data literal) must
    # not produce a chunk that blows past an embedding model's token limit.
    file = ProjectFile(path="minified.txt", content="x" * 100_000)

    chunks = chunk_file(file, max_chars=4000)

    assert all(len(c.text) <= 4000 for c in chunks)


def test_chunk_file_handles_empty_content():
    file = ProjectFile(path="empty.txt", content="")

    chunks = chunk_file(file)

    assert len(chunks) == 1
    assert chunks[0].text == ""


def test_chunk_file_falls_back_to_generic_splitter_for_unsupported_language():
    # An extension the code splitter doesn't know (e.g. Go) should behave
    # exactly like the generic .txt case above, not error out.
    file = ProjectFile(path="a.go", content="\n".join(f"line{i}" for i in range(10)))

    chunks = chunk_file(file, max_chars=4000)

    assert len(chunks) == 1
    assert chunks[0].text == file.content


def _python_source(n_functions: int) -> str:
    return "\n\n".join(f"def func_{i}(a, b):\n    return a + b" for i in range(n_functions))


def test_chunk_file_splits_python_at_function_boundaries(monkeypatch):
    monkeypatch.setattr(settings, "rag_chunk_overlap_chars", 0)
    file = ProjectFile(path="math_utils.py", content=_python_source(3))

    chunks = chunk_file(file, max_chars=40)

    assert len(chunks) > 1
    # Reconstructed line ranges must actually point back at the right text.
    lines = file.content.splitlines()
    for chunk in chunks:
        assert chunk.text.strip() in "\n".join(lines[chunk.start_line - 1 : chunk.end_line])


def test_chunk_file_splits_javascript_at_function_boundaries(monkeypatch):
    monkeypatch.setattr(settings, "rag_chunk_overlap_chars", 0)
    code = "\n\n".join(f"function fn{i}() {{\n  return {i};\n}}" for i in range(3))
    file = ProjectFile(path="utils.js", content=code)

    chunks = chunk_file(file, max_chars=40)

    assert len(chunks) > 1
    assert all(c.text.strip() for c in chunks)


def test_chunk_file_splits_typescript_at_function_boundaries(monkeypatch):
    monkeypatch.setattr(settings, "rag_chunk_overlap_chars", 0)
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
