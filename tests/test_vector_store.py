from app.ai.vector_store import rank_by_similarity_chroma


def test_rank_by_similarity_chroma_picks_best_matching_files():
    query = [1.0, 0.0]
    file_embeddings = {
        "auth.py": [[0.9, 0.1], [0.1, 0.9]],  # best chunk closely matches query
        "unrelated.py": [[0.0, 1.0], [-1.0, 0.0]],  # neither chunk matches
        "users.py": [[0.5, 0.5]],  # partial match
    }

    ranked = rank_by_similarity_chroma(file_embeddings, query, top_n=2)

    assert ranked == ["auth.py", "users.py"]


def test_rank_by_similarity_chroma_uses_best_chunk_not_average():
    query = [1.0, 0.0]
    file_embeddings = {
        # One great chunk and one terrible chunk should still beat a file of
        # uniformly mediocre chunks.
        "mixed.py": [[1.0, 0.0], [-1.0, 0.0]],
        "mediocre.py": [[0.5, 0.5], [0.5, 0.5]],
    }

    ranked = rank_by_similarity_chroma(file_embeddings, query, top_n=1)

    assert ranked == ["mixed.py"]


def test_rank_by_similarity_chroma_handles_file_with_no_chunks():
    # An empty file (or one whose only chunk was filtered out as blank) has no
    # chunks to score — it should rank last, not crash on an empty query.
    query = [1.0, 0.0]
    file_embeddings = {
        "empty.py": [],
        "real.py": [[0.0, 1.0]],
    }

    ranked = rank_by_similarity_chroma(file_embeddings, query, top_n=2)

    assert ranked == ["real.py", "empty.py"]
