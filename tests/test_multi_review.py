from app.review.multi import parse_file_edits


def test_parse_file_edits_returns_empty_when_no_markers():
    assert parse_file_edits("no changes needed", {"a.py": "x = 1\n"}) == []


def test_parse_file_edits_skips_unchanged_files():
    originals = {"a.py": "x = 1\n"}
    text = "=== a.py ===\nx = 1\n"

    assert parse_file_edits(text, originals) == []


def test_parse_file_edits_skips_unknown_paths():
    text = "=== unknown.py ===\nx = 2\n"

    assert parse_file_edits(text, {"a.py": "x = 1\n"}) == []


def test_parse_file_edits_returns_diff_for_changed_file():
    originals = {"a.py": "x = 1\n", "b.py": "y = 1\n"}
    text = "=== a.py ===\nx = 2\n"

    edits = parse_file_edits(text, originals)

    assert len(edits) == 1
    assert edits[0].path == "a.py"
    assert edits[0].output == "x = 2"
    assert "+x = 2" in edits[0].diff


def test_parse_file_edits_handles_multiple_files():
    originals = {"a.py": "x = 1\n", "b.py": "y = 1\n"}
    text = "=== a.py ===\nx = 2\n\n=== b.py ===\ny = 2\n"

    edits = parse_file_edits(text, originals)

    assert {e.path for e in edits} == {"a.py", "b.py"}
