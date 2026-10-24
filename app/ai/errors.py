from contextlib import contextmanager

import openai
from fastapi import HTTPException, status
from langgraph.errors import GraphRecursionError


@contextmanager
def translate_ai_errors():
    """Maps failures from the LLM call or the agent loop to a clean HTTP
    response, instead of letting them fall through as an opaque 500 (verified
    against a real OpenAI call: an auth failure raises openai.AuthenticationError
    with a 401 status_code, so these are genuine exception types, not guessed).
    """
    try:
        yield
    except GraphRecursionError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The assistant couldn't finish within its step budget. Try a narrower instruction or fewer files.",
        ) from error
    except openai.RateLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limited by the AI provider. Try again shortly.",
        ) from error
    except openai.AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider rejected the server's credentials.",
        ) from error
    except openai.BadRequestError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The AI provider rejected this request (e.g. input too large).",
        ) from error
    except openai.APIConnectionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the AI provider. Try again shortly.",
        ) from error
    except openai.OpenAIError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider returned an error.",
        ) from error