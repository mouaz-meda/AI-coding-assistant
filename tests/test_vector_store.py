from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.ai.vector_store import index_files, search_relevant_paths
from app.schemas.ingestion import ProjectFile


class _WordCountEmbeddings(Embeddings):
    """Deterministic fake embedding — no network call. Each dimension counts
    occurrences of one fixed vocabulary word, so texts sharing words end up
    closer together in cosine space."""

    VOCAB = ["login", "logout", "render", "button", "auth", "token", "unrelated"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)

    def _vec(self, text: str) -> list[float]:
        lowered = text.lower()
        return [float(lowered.count(word)) for word in self.VOCAB]


def _vector_store(tmp_path, name="test") -> Chroma:
    return Chroma(
        collection_name=name,
        embedding_function=_WordCountEmbeddings(),
        persist_directory=str(tmp_path),
        collection_metadata={"hnsw:space": "cosine"},
    )


def test_index_files_then_search_returns_best_matching_file(tmp_path):
    vector_store = _vector_store(tmp_path)
    files = [
        ProjectFile(path="auth.py", content="def login(user, token): pass"),
        ProjectFile(path="ui.py", content="def render_button(): pass"),
    ]
    index_files(vector_store, files)

    ranked = search_relevant_paths(vector_store, "login token auth", ["auth.py", "ui.py"], top_n=2)

    assert ranked[0] == "auth.py"


def test_search_relevant_paths_only_considers_available_paths(tmp_path):
    vector_store = _vector_store(tmp_path, name="scoped")
    files = [
        ProjectFile(path="auth.py", content="def login(user, token): pass"),
        ProjectFile(path="other_auth.py", content="def login(user, token): pass"),
    ]
    index_files(vector_store, files)

    ranked = search_relevant_paths(vector_store, "login token", ["auth.py"], top_n=5)

    assert ranked == ["auth.py"]


def test_index_files_is_idempotent_for_unchanged_content(tmp_path):
    vector_store = _vector_store(tmp_path, name="idempotent")
    files = [ProjectFile(path="auth.py", content="def login(): pass")]

    index_files(vector_store, files)
    index_files(vector_store, files)  # re-indexing unchanged content shouldn't duplicate

    assert vector_store._collection.count() == 1


def test_index_files_skips_blank_chunks(tmp_path):
    vector_store = _vector_store(tmp_path, name="blank")
    files = [ProjectFile(path="empty.py", content="")]

    index_files(vector_store, files)

    assert vector_store._collection.count() == 0
