import hashlib
import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.ai.chunking import chunk_file
from app.config import settings
from app.schemas.ingestion import ProjectFile

logger = logging.getLogger(__name__)


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
        logger.info("embedding + upserting %d chunk(s) from %d file(s):", len(documents), len(files))
        for doc, doc_id in zip(documents, ids):
            logger.info("    %s  (%d chars)  id=%s", doc.metadata["path"], len(doc.page_content), doc_id[:8])
        vector_store.add_documents(documents, ids=ids)
    else:
        logger.info("no chunks to index from %d file(s)", len(files))


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
    logger.info("similarity search query=%r over %d path(s) → %s", query, len(available_paths), ranked[:top_n])
    return ranked[:top_n]
