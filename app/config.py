from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Coding Assistant"
    port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    secret_key: str = "dev-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30  # currently unused — see app/auth/security.py
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    # Separate from the openai_* settings above so chat and embeddings can use
    # different providers (e.g. real OpenAI for chat, a local Ollama model for
    # embeddings) without one config overloading the other.
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str = ""
    ingest_root: str = ""
    max_file_bytes: int = 200_000
    max_files: int = 1000
    # Naive RAG (Phase 11): chunk size/overlap for scoring file relevance, and how
    # many of the most relevant files a multi-file request actually sends to the LLM.
    rag_chunk_lines: int = 40
    rag_chunk_overlap: int = 5
    # ~1000 tokens for most tokenizers — safely under an 8192-token embedding
    # limit even for dense/minified code, regardless of how long individual
    # lines are (rag_chunk_lines alone doesn't bound that).
    rag_chunk_max_chars: int = 4000
    rag_top_files: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
