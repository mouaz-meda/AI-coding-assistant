import itertools
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


def _run_with_responses(responses, files, action="review", instruction="check it"):
    model = FakeToolCallingModel(messages=iter(responses))
    with (
        patch("app.ai.agent.ChatOpenAI", return_value=model),
        patch("app.ai.agent.get_user_vector_store", return_value=None),
        patch("app.ai.agent.index_files"),
    ):
        return run_agentic_review(user_id=1, files=files, action=action, instruction=instruction)


def test_read_file_tool_returns_content_and_records_path():
    read_paths: list[str] = []
    _, read_file_tool = _build_tools(vector_store=None, files_by_path={"a.py": "x = 1"}, read_paths=read_paths)

    assert read_file_tool.invoke({"path": "a.py"}) == "x = 1"
    assert read_paths == ["a.py"]


def test_read_file_tool_reports_unknown_path():
    read_paths: list[str] = []
    _, read_file_tool = _build_tools(vector_store=None, files_by_path={"a.py": "x = 1"}, read_paths=read_paths)

    result = read_file_tool.invoke({"path": "missing.py"})

    assert "No file at path 'missing.py'" in result
    assert read_paths == []


def test_search_files_tool_delegates_to_search_relevant_paths():
    search_files_tool, _ = _build_tools(
        vector_store="fake-store", files_by_path={"a.py": "x", "b.py": "y"}, read_paths=[]
    )

    with patch("app.ai.agent.search_relevant_paths", return_value=["a.py"]) as mock_search:
        result = search_files_tool.invoke({"query": "auth", "top_n": 3})

    assert result == ["a.py"]
    mock_search.assert_called_once_with("fake-store", "auth", ["a.py", "b.py"], 3)


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
