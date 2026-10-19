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
# well enough to split along real boundaries instead of generic separators.
# More languages can be added here later; anything else falls back to the
# plain character splitter below.
_LANGUAGE_BY_EXTENSION = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
}


def chunk_file(file: ProjectFile, max_chars: int | None = None) -> list[Chunk]:
    if not file.content:
        return [Chunk(path=file.path, text="", start_line=1, end_line=1)]

    language = _LANGUAGE_BY_EXTENSION.get(Path(file.path).suffix)
    chunk_size = max_chars or settings.rag_chunk_max_chars
    splitter = (
        RecursiveCharacterTextSplitter.from_language(
            language=language, chunk_size=chunk_size, chunk_overlap=settings.rag_chunk_overlap_chars, add_start_index=True
        )
        if language is not None
        else RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=settings.rag_chunk_overlap_chars, add_start_index=True
        )
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
