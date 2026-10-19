import itertools
from contextlib import ExitStack
from unittest.mock import patch

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.errors import GraphRecursionError

from app.ai.agent import _build_tools, run_agentic_review
from app.schemas.ingestion import ProjectFile


class FakeToolCallingModel(GenericFakeChatModel):
    """GenericFakeChatModel plays back a canned script of messages but doesn't
    implement bind_tools (that's provider-specific) — create_agent calls it
    unconditionally, so tests need this trivial override to make the fake
    usable as a tool-calling model."""

    def bind_tools(self, tools, **kwargs):
        return self


def _run_with_responses(responses, files, action="review", instruction="check it", candidate_paths=None):
    model = FakeToolCallingModel(messages=iter(responses))
    patches = [
        patch("app.ai.agent.ChatOpenAI", return_value=model),
        patch("app.ai.agent.get_user_vector_store", return_value=None),
        patch("app.ai.agent.index_files"),
    ]
    if candidate_paths is not None:
        patches.append(patch("app.ai.agent._select_candidate_paths", return_value=candidate_paths))
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        return run_agentic_review(user_id=1, files=files, action=action, instruction=instruction)


def test_read_file_tool_returns_content_and_records_path():
    read_paths: list[str] = []
    _, read_file_tool = _build_tools(
        vector_store=None, files_by_path={"a.py": "x = 1"}, search_paths=["a.py"], read_paths=read_paths
    )

    assert read_file_tool.invoke({"path": "a.py"}) == "x = 1"
    assert read_paths == ["a.py"]


def test_read_file_tool_reports_unknown_path():
    read_paths: list[str] = []
    _, read_file_tool = _build_tools(
        vector_store=None, files_by_path={"a.py": "x = 1"}, search_paths=["a.py"], read_paths=read_paths
    )

    result = read_file_tool.invoke({"path": "missing.py"})

    assert "No file at path 'missing.py'" in result
    assert read_paths == []


def test_read_file_tool_reaches_files_outside_the_search_scope():
    # The safety valve: read_file isn't limited to the pre-selected candidate
    # files, only search_files is — so a file the selection step skipped is
    # still directly readable by exact path.
    read_paths: list[str] = []
    _, read_file_tool = _build_tools(
        vector_store=None,
        files_by_path={"a.py": "x = 1", "b.py": "y = 2"},
        search_paths=["a.py"],
        read_paths=read_paths,
    )

    assert read_file_tool.invoke({"path": "b.py"}) == "y = 2"
    assert read_paths == ["b.py"]


def test_search_files_tool_delegates_to_search_relevant_paths():
    # search_paths (the pre-selected candidates) is what gets passed to the
    # search, not every path in files_by_path — proves the two are scoped
    # independently.
    search_files_tool, _ = _build_tools(
        vector_store="fake-store",
        files_by_path={"a.py": "x", "b.py": "y", "c.py": "z"},
        search_paths=["a.py", "b.py"],
        read_paths=[],
    )

    with patch("app.ai.agent.search_relevant_paths", return_value=["a.py"]) as mock_search:
        result = search_files_tool.invoke({"query": "auth", "top_n": 3})

    assert result == ["a.py"]
    mock_search.assert_called_once_with("fake-store", "auth", ["a.py", "b.py"], 3)


def test_run_agentic_review_only_indexes_selected_candidate_files():
    files = [ProjectFile(path="a.py", content="x = 1\n"), ProjectFile(path="b.py", content="y = 2\n")]
    responses = [AIMessage(content="No files needed looking at.")]
    model = FakeToolCallingModel(messages=iter(responses))

    with (
        patch("app.ai.agent.ChatOpenAI", return_value=model),
        patch("app.ai.agent.get_user_vector_store", return_value=None),
        patch("app.ai.agent.index_files") as mock_index,
        patch("app.ai.agent._select_candidate_paths", return_value=["a.py"]),
    ):
        run_agentic_review(user_id=1, files=files, action="review", instruction="check it")

    indexed_files = mock_index.call_args[0][1]
    assert [f.path for f in indexed_files] == ["a.py"]


def test_run_agentic_review_read_file_reaches_a_non_candidate_file():
    files = [ProjectFile(path="a.py", content="x = 1\n"), ProjectFile(path="b.py", content="y = 2\n")]
    responses = [
        AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"path": "b.py"}, "id": "call_1"}]),
        AIMessage(content="b.py looks fine."),
    ]

    reply, read_paths = _run_with_responses(responses, files, candidate_paths=["a.py"])

    assert reply == "b.py looks fine."
    assert read_paths == ["b.py"]


def test_select_candidate_paths_skips_the_model_call_when_within_top_n():
    from app.ai.agent import _select_candidate_paths

    with patch("app.ai.agent.ChatOpenAI") as mock_model:
        result = _select_candidate_paths(["a.py", "b.py"], "review", "check it", top_n=5)

    mock_model.assert_not_called()
    assert result == ["a.py", "b.py"]


def test_run_agentic_review_executes_read_file_then_returns_final_answer():
    files = [ProjectFile(path="a.py", content="x = 1\n")]
    responses = [
        AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"path": "a.py"}, "id": "call_1"}]),
        AIMessage(content="x = 1 looks fine."),
    ]

    reply, read_paths = _run_with_responses(responses, files)

    assert reply == "x = 1 looks fine."
    assert read_paths == ["a.py"]


def test_run_agentic_review_stops_immediately_when_no_tool_call():
    files = [ProjectFile(path="a.py", content="x = 1\n")]
    responses = [AIMessage(content="No files needed looking at.")]

    reply, read_paths = _run_with_responses(responses, files)

    assert reply == "No files needed looking at."
    assert read_paths == []


def test_run_agentic_review_fix_returns_structured_edits():
    files = [ProjectFile(path="a.py", content="x = 1\n"), ProjectFile(path="b.py", content="y = 2\n")]
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "FixEdits",
                    "args": {"edits": [{"path": "a.py", "content": "x = 2\n"}]},
                    "id": "call_1",
                }
            ],
        )
    ]

    edits, _ = _run_with_responses(responses, files, action="fix", candidate_paths=["a.py", "b.py"])

    assert len(edits) == 1
    assert edits[0].path == "a.py"
    assert edits[0].output == "x = 2\n"
    assert "+x = 2" in edits[0].diff


def test_run_agentic_review_fix_skips_unknown_and_unchanged_files():
    files = [ProjectFile(path="a.py", content="x = 1\n")]
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "FixEdits",
                    "args": {
                        "edits": [
                            {"path": "a.py", "content": "x = 1\n"},  # unchanged
                            {"path": "unknown.py", "content": "z = 1\n"},  # not in request
                        ]
                    },
                    "id": "call_1",
                }
            ],
        )
    ]

    edits, _ = _run_with_responses(responses, files, action="fix", candidate_paths=["a.py"])

    assert edits == []


def test_run_agentic_review_raises_when_recursion_limit_exceeded(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "agent_recursion_limit", 2)
    files = [ProjectFile(path="a.py", content="x = 1\n")]

    def endless():
        while True:
            yield AIMessage(
                content="", tool_calls=[{"name": "read_file", "args": {"path": "a.py"}, "id": "call_x"}]
            )

    with pytest.raises(GraphRecursionError):
        _run_with_responses(list(itertools.islice(endless(), 10)), files)
