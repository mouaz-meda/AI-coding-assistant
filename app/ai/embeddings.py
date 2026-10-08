import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def get_embeddings(texts: list[str]) -> list[list[float]]:
    # A separate client from llm.py's — embeddings have their own provider config
    # so they can run on a different endpoint (e.g. a local model) than chat does.
    client = OpenAI(api_key=settings.embedding_api_key, base_url=settings.embedding_base_url or None)
    base_url = settings.embedding_base_url or "https://api.openai.com/v1"

    logger.info("Requesting %d embedding(s) from %s (model=%s)", len(texts), base_url, settings.embedding_model)
    try:
        response = client.embeddings.create(model=settings.embedding_model, input=texts)
    except Exception:
        # Never log the API key — just enough context (model/endpoint/input count)
        # to tell a bad model name apart from an unreachable endpoint or a bad key.
        logger.exception("Embeddings call failed (%s, model=%s, inputs=%d)", base_url, settings.embedding_model, len(texts))
        raise

    logger.info("Received %d embedding(s) back from %s", len(response.data), base_url)
    return [item.embedding for item in response.data]
