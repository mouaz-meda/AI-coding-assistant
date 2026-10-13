import uuid

import chromadb


def rank_by_similarity_chroma(
    file_embeddings: dict[str, list[list[float]]],
    query_embedding: list[float],
    top_n: int,
) -> list[str]:
    """Chroma-backed drop-in for rank_by_similarity (app/ai/retrieval.py) — same
    interface, same "best chunk per file, not average" semantics, but storage and
    nearest-neighbor search are delegated to Chroma instead of a manual numpy loop.

    Ephemeral: chromadb.Client() with no path keeps everything in memory for the
    lifetime of this call only. No persistence across requests — Phase 11's
    in-memory version already re-embedded every request, so this doesn't lose
    anything that existed before. Persisting chunks across requests is deferred
    (needs a stable content identity ingestion doesn't have yet).
    """
    paths_with_chunks = [path for path, chunks in file_embeddings.items() if chunks]
    if not paths_with_chunks:
        return list(file_embeddings)[:top_n]

    # chromadb.Client() shares its in-memory store across calls within a process,
    # so each call needs its own collection name to avoid colliding with (or
    # reusing stale data from) a previous call.
    client = chromadb.Client()
    collection = client.create_collection(name=f"relevance-{uuid.uuid4()}", metadata={"hnsw:space": "cosine"})

    ids, embeddings, metadatas = [], [], []
    for path in paths_with_chunks:
        for i, chunk in enumerate(file_embeddings[path]):
            ids.append(f"{path}::{i}")
            embeddings.append(chunk)
            metadatas.append({"path": path})
    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    # Ask for every chunk, not just top_n — several of the nearest chunks can
    # belong to the same file, and we want each file's single best chunk only.
    result = collection.query(query_embeddings=[query_embedding], n_results=len(ids))

    best_distance: dict[str, float] = {}
    for metadata, distance in zip(result["metadatas"][0], result["distances"][0]):
        path = metadata["path"]
        if path not in best_distance or distance < best_distance[path]:
            best_distance[path] = distance

    ranked = sorted(best_distance, key=lambda path: best_distance[path])
    missing = [path for path in file_embeddings if path not in best_distance]
    return (ranked + missing)[:top_n]
