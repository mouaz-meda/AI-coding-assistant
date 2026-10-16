from dataclasses import dataclass
from pathlib import Path

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from app.config import settings
from app.schemas.ingestion import ProjectFile


@dataclass
class Chunk:
    path: str
    text: str
    start_line: int
    end_line: int


# LangChain's splitter understands these languages' syntax (functions/classes)
# well enough to split along real boundaries instead of a fixed line count.
# More languages can be added here later; anything else falls back to the
# generic line-based splitter below.
_LANGUAGE_BY_EXTENSION = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
}


def chunk_file(
    file: ProjectFile,
    chunk_lines: int | None = None,
    overlap: int | None = None,
    max_chars: int | None = None,
) -> list[Chunk]:
    language = _LANGUAGE_BY_EXTENSION.get(Path(file.path).suffix)
    if language is not None:
        return _chunk_by_language(file, language, max_chars or settings.rag_chunk_max_chars)
    return _chunk_by_lines(file, chunk_lines, overlap, max_chars)


def _chunk_by_language(file: ProjectFile, language: Language, chunk_size: int) -> list[Chunk]:
    if not file.content:
        return [Chunk(path=file.path, text="", start_line=1, end_line=1)]

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=chunk_size,
        chunk_overlap=settings.rag_code_chunk_overlap_chars,
        add_start_index=True,
    )
    chunks = []
    for doc in splitter.create_documents([file.content]):
        start = doc.metadata["start_index"]
        end = start + len(doc.page_content)
        chunks.append(
            Chunk(
                path=file.path,
                text=doc.page_content,
                start_line=file.content.count("\n", 0, start) + 1,
                end_line=file.content.count("\n", 0, end) + 1,
            )
        )
    return chunks


def _chunk_by_lines(
    file: ProjectFile,
    chunk_lines: int | None,
    overlap: int | None,
    max_chars: int | None,
) -> list[Chunk]:
    """Fixed-size line windows — the fallback for any language the splitter
    above doesn't know yet. Simple and language-agnostic.

    Line count alone isn't a safe size bound — a handful of long lines
    (minified JS, a generated file, a long data literal) can still blow past
    an embedding model's token limit. max_chars truncates each chunk's text
    as a model-agnostic safety net (no tokenizer dependency, just a
    conservative character cap); start_line/end_line still describe the full
    window, not just the kept text, since nothing downstream reads them yet.

    A chunk's end is also nudged back to the nearest blank line within the
    overlap region, if one exists, instead of always cutting at a hard line
    count — avoids ending a chunk mid-function/mid-class in the common case.
    Only searching within the overlap region is what keeps this safe: the
    next chunk always starts there anyway, so trimming this chunk's tail
    there can never skip a line.
    """
    chunk_lines = chunk_lines or settings.rag_chunk_lines
    overlap = overlap if overlap is not None else settings.rag_chunk_overlap
    max_chars = max_chars or settings.rag_chunk_max_chars

    lines = file.content.splitlines()
    if not lines:
        return [Chunk(path=file.path, text="", start_line=1, end_line=1)]

    step = chunk_lines - overlap
    chunks = []
    start = 0
    while start < len(lines):
        raw_end = min(start + chunk_lines, len(lines))
        end = raw_end if raw_end == len(lines) else _snap_to_blank_line(lines, raw_end, overlap)
        chunks.append(
            Chunk(
                path=file.path,
                text="\n".join(lines[start:end])[:max_chars],
                start_line=start + 1,
                end_line=end,
            )
        )
        if raw_end == len(lines):
            break
        start += step
    return chunks


def _snap_to_blank_line(lines: list[str], end: int, search_window: int) -> int:
    earliest = max(0, end - search_window)
    for i in range(end - 1, earliest - 1, -1):
        if not lines[i].strip():
            return i + 1
    return end
