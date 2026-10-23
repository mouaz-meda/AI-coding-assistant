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
    "project. The full content of the file(s) most likely relevant to this "
    "instruction is already included in the user message below — that content "
    "is final, never call a tool to re-read one of those files. If you need a "
    "file not shown there, use search_files to find it among the request's "
    "other files, then read_file to see its full content before referencing or "
    "changing it. Never guess at a file's content without reading it first, "
    "and never call the same tool with the same arguments more than once.\n\n"
    "When you are ready to give your final answer, stop calling tools, and "
    "submit your final answer with exactly ONE call to the structured response "
    "tool — never call it more than once, and never call it separately per "
    "file:\n"
    '- For a "review": the findings list contains one entry per file that has '
    "feedback (skip files with nothing to note), each with that file's notes. "
    "Use general for feedback that isn't about one specific file. Do not "
    "rewrite any file.\n"
    '- For a "fix": the edits list contains every changed file as one item '
    "each, each with its full new content. Include only files whose content "
    "actually changed."
)


class FileFix(BaseModel):
    path: str
    content: str


class FixEdits(BaseModel):
    """Final answer for a "fix" action — the full new content of every file
    whose content actually changed. Do not include unchanged files."""

    edits: list[FileFix]


class FileReview(BaseModel):
    path: str
    notes: str


class ReviewFindings(BaseModel):
    """Final answer for a "review" action — findings grouped per file, so the
    UI can show each file's feedback separately instead of one wall of text."""

    general: str = ""
    findings: list[FileReview] = []


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
        if path not in read_paths:  # already preloaded or already read — don't double-count
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
) -> tuple[ReviewFindings | list[FileEdit], list[str]]:
    """Feeds the model the pre-selected candidates' content directly (no tool
    round trip needed to fetch what we already loaded into memory to index
    them), while still letting it drive retrieval itself via tool calls for
    anything outside that set. Returns (review text, or fix edits; paths
    actually considered)."""
    files_by_path = {f.path: f.content for f in files}
    candidate_paths = _select_candidate_paths(list(files_by_path), action, instruction, settings.rag_top_files)
    candidate_files = [f for f in files if f.path in candidate_paths]
    other_paths = [p for p in files_by_path if p not in candidate_paths]

    vector_store = get_user_vector_store(user_id)
    print(f"{AGENT}[agent] indexing {len(candidate_files)} candidate file(s) for user {user_id}{RESET}")
    index_files(vector_store, candidate_files)

    # Seeded with the candidates: their content is handed to the model below,
    # so they're already "considered" without a read_file round trip.
    read_paths: list[str] = list(candidate_paths)
    # Confirmed against the real model (not guessed): handing it search_files/
    # read_file when every file is already preloaded below tempts it into
    # redundantly re-reading files it already has, looping until the
    # recursion limit is hit instead of ever answering. No other_paths means
    # there is nothing those tools could usefully reach, so skip binding them.
    tools = _build_tools(vector_store, files_by_path, candidate_paths, read_paths) if other_paths else []

    agent = create_agent(
        model=_build_chat_model(),
        tools=tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
        response_format=FixEdits if action == "fix" else ReviewFindings,
    )

    candidate_block = "\n\n".join(f"=== {f.path} ===\n{f.content}" for f in candidate_files)
    print(
        f"{AGENT}[agent] invoking agent → action={action}, files={len(files)}, "
        f"preloaded={len(candidate_files)}, recursion_limit={settings.agent_recursion_limit}{RESET}"
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Action: {action}\nInstruction: {instruction}\n\n"
                        f"Full content of the file(s) most likely relevant to this "
                        f"instruction:\n\n{candidate_block}\n\n"
                        "Other files in this request (use read_file by exact path if "
                        f"you need one): {', '.join(other_paths) if other_paths else '(none)'}"
                    ),
                }
            ]
        },
        config={"recursion_limit": settings.agent_recursion_limit},
    )

    if action == "fix":
        edits = _build_edits(result["structured_response"].edits, files_by_path)
        print(f"{AGENT}[agent] final edits (considered={read_paths}): {[e.path for e in edits]}{RESET}")
        return edits, read_paths

    findings: ReviewFindings = result["structured_response"]
    print(
        f"{AGENT}[agent] final findings (considered={read_paths}): "
        f"{[f.path for f in findings.findings]}, general={bool(findings.general)}{RESET}"
    )
    return findings, read_paths


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
