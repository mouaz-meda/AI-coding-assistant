from app.ai.chunking import chunk_file
from app.schemas.ingestion import ProjectFile


def test_chunk_file_returns_single_chunk_when_shorter_than_chunk_size():
    file = ProjectFile(path="a.py", content="\n".join(f"line{i}" for i in range(10)))

    chunks = chunk_file(file, chunk_lines=40, overlap=5)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 10
    assert chunks[0].text == file.content


def test_chunk_file_splits_with_overlap():
    file = ProjectFile(path="a.py", content="\n".join(f"line{i}" for i in range(25)))

    chunks = chunk_file(file, chunk_lines=10, overlap=2)

    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 10), (9, 18), (17, 25)]
    # Overlapping lines actually appear in both neighboring chunks.
    assert "line8" in chunks[0].text
    assert "line8" in chunks[1].text


def test_chunk_file_handles_empty_content():
    file = ProjectFile(path="empty.py", content="")

    chunks = chunk_file(file)

    assert len(chunks) == 1
    assert chunks[0].text == ""


def test_chunk_file_caps_chunk_length_even_with_few_long_lines():
    # A handful of very long lines (minified code, a long data literal) must
    # not produce a chunk that blows past an embedding model's token limit.
    file = ProjectFile(path="minified.js", content="x" * 100_000)

    chunks = chunk_file(file, chunk_lines=40, overlap=5, max_chars=4000)

    assert all(len(c.text) <= 4000 for c in chunks)


def test_chunk_file_snaps_end_to_nearby_blank_line():
    # Blank line at index 3 falls inside the overlap search window for the
    # first chunk's natural cut point (index 5) — the chunk should end right
    # after it instead of continuing into the next block.
    lines = ["a", "b", "c", "", "d", "e", "f", "g", "h", "i"]
    file = ProjectFile(path="a.py", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    assert chunks[0].end_line == 4
    assert chunks[0].text == "a\nb\nc\n"


def test_chunk_file_snapping_never_skips_a_line():
    # Even with snapping shortening some chunks, every line must still appear
    # in at least one chunk — a coverage gap would mean that content can
    # never be found by retrieval at all.
    lines = ["a", "b", "c", "", "d", "e", "f", "g", "h", "i"]
    file = ProjectFile(path="a.py", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    covered = set()
    for c in chunks:
        covered.update(range(c.start_line, c.end_line + 1))
    assert covered == set(range(1, len(lines) + 1))


def test_chunk_file_falls_back_to_hard_cut_when_no_blank_line_nearby():
    lines = [f"line{i}" for i in range(10)]  # no blank lines at all
    file = ProjectFile(path="a.py", content="\n".join(lines))

    chunks = chunk_file(file, chunk_lines=5, overlap=2)

    # Unchanged from the pre-snapping behavior: hard cut at chunk_lines.
    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 5), (4, 8), (7, 10)]