import httpx
import openai
import pytest
from fastapi import HTTPException
from langgraph.errors import GraphRecursionError

from app.ai.errors import translate_ai_errors

_REQUEST = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


def _response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=_REQUEST, json={"error": {"message": "x"}})


@pytest.mark.parametrize(
    "raised,expected_status",
    [
        (GraphRecursionError("limit"), 500),
        (openai.RateLimitError("rate limited", response=_response(429), body=None), 429),
        (openai.AuthenticationError("bad key", response=_response(401), body=None), 502),
        (openai.BadRequestError("bad request", response=_response(400), body=None), 400),
        (openai.APIConnectionError(request=_REQUEST), 503),
        (openai.APIError("generic", request=_REQUEST, body=None), 502),
    ],
)
def test_translate_ai_errors_maps_each_known_failure(raised, expected_status):
    with pytest.raises(HTTPException) as exc_info:
        with translate_ai_errors():
            raise raised

    assert exc_info.value.status_code == expected_status


def test_translate_ai_errors_leaves_other_exceptions_alone():
    with pytest.raises(ValueError):
        with translate_ai_errors():
            raise ValueError("unrelated")
