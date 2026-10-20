import hashlib

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.ai.chunking import chunk_file
from app.colors import RESET, VECTOR_STORE
from app.config import settings
from app.schemas.ingestion import ProjectFile


def get_user_vector_store(user_id: int) -> Chroma:
    """One persistent Chroma collection per user. Request files aren't tied to
    a persisted project (ingestion stays stateless, Phase 7), so without
    per-user scoping one user's search could surface another user's uploaded
    code."""
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url or None,
    )
    return Chroma(
        collection_name=f"user-{user_id}",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_directory,
        collection_metadata={"hnsw:space": "cosine"},
    )


def index_files(vector_store: Chroma, files: list[ProjectFile]) -> None:
    """Chunk and upsert every file's chunks. Each chunk's id is a hash of its
    path+text, so re-indexing unchanged content is a no-op (Chroma upserts by
    id) instead of growing the collection or re-embedding on every request."""
    documents, ids = [], []
    for file in files:
        for chunk in chunk_file(file):
            if not chunk.text.strip():
                continue
            documents.append(Document(page_content=chunk.text, metadata={"path": file.path}))
            ids.append(hashlib.sha256(f"{file.path}:{chunk.text}".encode()).hexdigest())
    if documents:
        print(f"{VECTOR_STORE}[vector_store] embedding + upserting {len(documents)} chunk(s) from {len(files)} file(s):{RESET}")
        for doc, doc_id in zip(documents, ids):
            print(f"{VECTOR_STORE}    {doc.metadata['path']}  ({len(doc.page_content)} chars)  id={doc_id[:8]}{RESET}")
        vector_store.add_documents(documents, ids=ids)
    else:
        print(f"{VECTOR_STORE}[vector_store] no chunks to index from {len(files)} file(s){RESET}")


def search_relevant_paths(
    vector_store: Chroma,
    query: str,
    available_paths: list[str],
    top_n: int,
) -> list[str]:
    """Best-matching chunk per file, restricted to this request's own files —
    the persisted collection accumulates chunks across requests, so results
    must be filtered back down to what's actually in play right now."""
    results = vector_store.similarity_search_with_score(
        query, k=max(top_n * 4, 20), filter={"path": {"$in": available_paths}}
    )
    ranked: list[str] = []
    for doc, _score in sorted(results, key=lambda pair: pair[1]):
        if doc.metadata["path"] not in ranked:
            ranked.append(doc.metadata["path"])
    print(
        f"{VECTOR_STORE}[vector_store] similarity search query={query!r} over "
        f"{len(available_paths)} path(s) → {ranked[:top_n]}{RESET}"
    )
    return ranked[:top_n]
