from typing import Literal

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI

from app.ai.llm import FILE_MARKER
from app.ai.vector_store import get_user_vector_store, index_files, search_relevant_paths
from app.config import settings
from app.schemas.ingestion import ProjectFile

AGENT_SYSTEM_PROMPT = (
    "You are an autonomous code-editing assistant working across a multi-file "
    "project. You do not see file contents up front — use the search_files tool "
    "to find files relevant to the instruction, then read_file to see a file's "
    "full content before referencing or changing it. Never guess at a file's "
    "content without reading it first.\n\n"
    "When you are ready to give your final answer, stop calling tools and reply "
    "with plain text only:\n"
    '- For a "review": describe your findings as plain text, referencing file '
    "paths where relevant. Do not rewrite any file.\n"
    '- For a "fix": only include files whose content actually changed. For each '
    f'changed file, output a line exactly as {FILE_MARKER.format(path="<path>")} '
    "followed by the file's full new content. Do not include unchanged files, "
    "explanations, commentary, or markdown code fences."
)


def _build_tools(vector_store: Chroma | None, files_by_path: dict[str, str], read_paths: list[str]):
    available_paths = list(files_by_path)

    @tool
    def search_files(query: str, top_n: int = settings.rag_top_files) -> list[str]:
        """Search this request's files for the ones most relevant to a query.

        Returns a ranked list of file paths. Use this to narrow down which
        files to look at before reading them in full.
        """
        return search_relevant_paths(vector_store, query, available_paths, top_n)

    @tool
    def read_file(path: str) -> str:
        """Read the full content of one file by its exact path."""
        content = files_by_path.get(path)
        if content is None:
            return f"No file at path '{path}'. Available paths: {', '.join(available_paths)}"
        read_paths.append(path)
        return content

    return [search_files, read_file]


def run_agentic_review(
    user_id: int,
    files: list[ProjectFile],
    action: Literal["review", "fix"],
    instruction: str,
) -> tuple[str, list[str]]:
    """Let the model drive retrieval itself via tool calls instead of us
    picking files upfront. Returns (final reply text, paths actually read)."""
    vector_store = get_user_vector_store(user_id)
    index_files(vector_store, files)

    files_by_path = {f.path: f.content for f in files}
    read_paths: list[str] = []
    tools = _build_tools(vector_store, files_by_path, read_paths)

    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    agent = create_agent(model=model, tools=tools, system_prompt=AGENT_SYSTEM_PROMPT)

    file_list = "\n".join(files_by_path)
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
    return result["messages"][-1].content, read_paths
