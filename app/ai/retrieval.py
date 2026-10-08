import numpy as np

from app.ai.chunking import chunk_file
from app.ai.embeddings import get_embeddings
from app.config import settings
from app.schemas.ingestion import ProjectFile


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_vec, b_vec = np.array(a), np.array(b)
    denom = np.linalg.norm(a_vec) * np.linalg.norm(b_vec)
    return float(np.dot(a_vec, b_vec) / denom) if denom else 0.0


def rank_by_similarity(
    file_embeddings: dict[str, list[list[float]]],
    query_embedding: list[float],
    top_n: int,
) -> list[str]:
    """Rank file paths by their most relevant chunk's similarity to the query.

    A file's score is its best-matching chunk, not an average — a large file
    with one highly relevant section shouldn't rank below a small file that's
    uniformly mediocre. Pure function: takes embeddings, not files, so it's
    testable without a real embeddings call.
    """
    scores = {
        path: max((cosine_similarity(chunk, query_embedding) for chunk in chunks), default=-1.0)
        for path, chunks in file_embeddings.items()
    }
    ranked = sorted(scores, key=lambda path: scores[path], reverse=True)
    return ranked[:top_n]


def select_relevant_files(
    files: list[ProjectFile],
    instruction: str,
    top_n: int | None = None,
) -> list[ProjectFile]:
    """Chunk + embed every file, then keep only the top_n most relevant to
    instruction. The only part of this module that makes a real embeddings call."""
    top_n = top_n or settings.rag_top_files

    # Skip empty/whitespace-only chunks — the embeddings API rejects empty
    # strings outright, and a blank chunk carries no relevance signal anyway.
    chunks_by_file = {f.path: [c for c in chunk_file(f) if c.text.strip()] for f in files}
    all_chunks = [chunk for chunks in chunks_by_file.values() for chunk in chunks]
    if not all_chunks:
        return files[:top_n]

    all_embeddings = get_embeddings([chunk.text for chunk in all_chunks])

    file_embeddings: dict[str, list[list[float]]] = {}
    i = 0
    for path, chunks in chunks_by_file.items():
        file_embeddings[path] = all_embeddings[i : i + len(chunks)]
        i += len(chunks)

    query_embedding = get_embeddings([instruction])[0]
    relevant_paths = set(rank_by_similarity(file_embeddings, query_embedding, top_n))
    return [f for f in files if f.path in relevant_paths]