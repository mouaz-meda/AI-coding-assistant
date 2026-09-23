from app.review.diff import make_diff


def test_make_diff_returns_empty_string_for_identical_content():
    original = "def add(a, b):\n    return a + b\n"

    assert make_diff("math.py", original, original) == ""


def test_make_diff_shows_added_and_removed_lines():
    original = "def add(a, b):\n    return a - b\n"
    fixed = "def add(a, b):\n    return a + b\n"

    diff = make_diff("math.py", original, fixed)

    assert "--- a/math.py" in diff
    assert "+++ b/math.py" in diff
    assert "-    return a - b" in diff
    assert "+    return a + b" in diff


def test_make_diff_handles_multiline_changes():
    original = "line1\nline2\nline3\n"
    fixed = "line1\nchanged2\nline3\nline4\n"

    diff = make_diff("file.txt", original, fixed)
    changed_lines = [line for line in diff.splitlines() if line.startswith(("+", "-"))]

    assert "-line2" in changed_lines
    assert "+changed2" in changed_lines
    assert "+line4" in changed_lines
    assert not any(line.endswith("line1") for line in changed_lines)
