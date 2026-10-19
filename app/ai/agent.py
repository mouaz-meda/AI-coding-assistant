from typing import Literal

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.ai.vector_store import get_user_vector_store, index_files, search_relevant_paths
from app.colors import AGENT, RESET
from app.config import settings
from app.review.diff import make_diff
from app.schemas.ingestion import ProjectFile
from app.schemas.review import FileEdit

AGENT_SYSTEM_PROMPT = (
    "You are an autonomous code-editing assistant working across a multi-file "
    "project. You do not see file contents up front — use the search_files tool "
    "to find files relevant to the instruction, then read_file to see a file's "
    "full content before referencing or changing it. Never guess at a file's "
    "content without reading it first.\n\n"
    "When you are ready to give your final answer, stop calling tools:\n"
    '- For a "review": reply with plain text describing your findings, '
    "referencing file paths where relevant. Do not rewrite any file.\n"
    '- For a "fix": submit your final answer through the structured response '
    "tool, including only the files whose content actually changed, each with "
    "its full new content."
)


class FileFix(BaseModel):
    path: str
    content: str


class FixEdits(BaseModel):
    """Final answer for a "fix" action — the full new content of every file
    whose content actually changed. Do not include unchanged files."""

    edits: list[FileFix]


def _build_tools(
    vector_store: Chroma | None,
    files_by_path: dict[str, str],
    search_paths: list[str],
    read_paths: list[str],
):
    @tool
    def search_files(query: str, top_n: int = settings.rag_top_files) -> list[str]:
        """Search this request's pre-selected files for the ones most relevant to a query.

        Returns a ranked list of file paths. Use this to narrow down which
        files to look at before reading them in full.
        """
        result = search_relevant_paths(vector_store, query, search_paths, top_n)
        print(f"{AGENT}[agent] tool call: search_files(query={query!r}, top_n={top_n}) → {result}{RESET}")
        return result

    @tool
    def read_file(path: str) -> str:
        """Read the full content of one file by its exact path. Not limited to
        the pre-selected files — any path from the available-files list works."""
        content = files_by_path.get(path)
        if content is None:
            print(f"{AGENT}[agent] tool call: read_file(path={path!r}) → not found{RESET}")
            return f"No file at path '{path}'. Available paths: {', '.join(files_by_path)}"
        print(f"{AGENT}[agent] tool call: read_file(path={path!r}) → {len(content)} chars{RESET}")
        read_paths.append(path)
        return content

    return [search_files, read_file]


def _build_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )


class _PathSelection(BaseModel):
    paths: list[str]


def _select_candidate_paths(paths: list[str], action: str, instruction: str, top_n: int) -> list[str]:
    """Cheap upfront filter, on filenames alone, before any chunking/embedding
    happens: picks which files are worth indexing for this request. Chunk-level
    search (search_files) then only ranks within files already known to
    matter, instead of scoring every uploaded file's chunks blindly.

    Advisory only — read_file still works on any path in the request (see
    _build_tools), so a wrong or too-narrow pick here doesn't cut the agent
    off from a file it turns out to need.
    """
    if len(paths) <= top_n:
        print(f"{AGENT}[agent] path-selection call skipped — only {len(paths)} file(s), top_n={top_n}{RESET}")
        return paths

    print(f"{AGENT}[agent] path-selection call → model={settings.openai_model}, {len(paths)} candidate paths{RESET}")
    selector = _build_chat_model().with_structured_output(_PathSelection)
    prompt = (
        f"Action: {action}\nInstruction: {instruction}\n\n"
        f"Pick up to {top_n} file paths from the list below that are most likely "
        "relevant to this task. Only return paths from this list.\n\n"
        "Paths:\n" + "\n".join(paths)
    )
    result = selector.invoke(prompt)
    selected = [p for p in result.paths if p in paths][:top_n]
    print(f"{AGENT}[agent] path-selection result → {selected or paths}{RESET}")
    return selected or paths


def run_agentic_review(
    user_id: int,
    files: list[ProjectFile],
    action: Literal["review", "fix"],
    instruction: str,
) -> tuple[str | list[FileEdit], list[str]]:
    """Let the model drive retrieval itself via tool calls instead of us
    picking files upfront. Returns (review text, or fix edits; paths actually
    read)."""
    files_by_path = {f.path: f.content for f in files}
    candidate_paths = _select_candidate_paths(list(files_by_path), action, instruction, settings.rag_top_files)
    candidate_files = [f for f in files if f.path in candidate_paths]

    vector_store = get_user_vector_store(user_id)
    print(f"{AGENT}[agent] indexing {len(candidate_files)} candidate file(s) for user {user_id}{RESET}")
    index_files(vector_store, candidate_files)

    read_paths: list[str] = []
    tools = _build_tools(vector_store, files_by_path, candidate_paths, read_paths)

    agent = create_agent(
        model=_build_chat_model(),
        tools=tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
        response_format=FixEdits if action == "fix" else None,
    )

    file_list = "\n".join(files_by_path)
    print(
        f"{AGENT}[agent] invoking agent → action={action}, files={len(files)}, "
        f"recursion_limit={settings.agent_recursion_limit}{RESET}"
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Action: {action}\nInstruction: {instruction}\n\n"
                    f"Available files ({len(files)}):\n{file_list}",
                }
            ]
        },
        config={"recursion_limit": settings.agent_recursion_limit},
    )

    if action == "fix":
        edits = _build_edits(result["structured_response"].edits, files_by_path)
        print(f"{AGENT}[agent] final edits (read_paths={read_paths}): {[e.path for e in edits]}{RESET}")
        return edits, read_paths

    reply = result["messages"][-1].content
    print(
        f"{AGENT}[agent] final answer ({len(reply)} chars, read_paths={read_paths}):\n"
        f"{'-' * 60}\n{reply}\n{'-' * 60}{RESET}"
    )
    return reply, read_paths


def _build_edits(fixes: list[FileFix], files_by_path: dict[str, str]) -> list[FileEdit]:
    """Drop files the model referenced that aren't in the request, and files
    whose content didn't actually change — the model's own judgment of
    "changed" isn't trusted blindly."""
    edits = []
    for fix in fixes:
        original = files_by_path.get(fix.path)
        if original is None or fix.content.rstrip("\n") == original.rstrip("\n"):
            continue
        edits.append(FileEdit(path=fix.path, output=fix.content, diff=make_diff(fix.path, original, fix.content)))
    return edits
