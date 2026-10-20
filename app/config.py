from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Coding Assistant"
    port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    secret_key: str = "dev-secret-key-change-me"
    algorithm: str = "HS256"
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
    # Naive RAG (Phase 11): chunk size for scoring file relevance, and how many
    # of the most relevant files a multi-file request actually sends to the LLM.
    # ~1000 tokens for most tokenizers — safely under an 8192-token embedding
    # limit even for dense/minified code.
    rag_chunk_max_chars: int = 4000
    rag_top_files: int = 5
    # LangChain's RecursiveCharacterTextSplitter's overlap, in characters —
    # shared by both the code-aware splitter and the generic fallback.
    rag_chunk_overlap_chars: int = 200
    # Phase 12 (LangChain/Chroma): persistent, per-user vector store location.
    chroma_persist_directory: str = "./data/chroma"
    # Phase 13 (LangChain agent): langgraph recursion limit on the tool-calling
    # loop. Each round trip costs 2 graph steps (model, then tools), so this
    # caps the agent at roughly 6 tool-calling round trips before it's forced
    # to stop (raises GraphRecursionError rather than a graceful final answer).
    agent_recursion_limit: int = 12

    class Config:
        env_file = ".env"


settings = Settings()
