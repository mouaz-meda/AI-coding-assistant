import logging
from typing import Literal

from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class LoggingCallback(BaseCallbackHandler):
    """Gives any ChatOpenAI instance the same call/response visibility
    get_chat_response prints below — for model calls made elsewhere (the
    agent's tool-calling loop, path-selection) that don't go through that
    function. Attach via callbacks=[LoggingCallback()] when building a model.
    """

    def on_chat_model_start(self, serialized, messages, **kwargs):
        chars = sum(len(m.content) for batch in messages for m in batch if isinstance(m.content, str))
        logger.info("chat completion call → model=%s, message_chars=%d", settings.openai_model, chars)

    def on_llm_end(self, response, **kwargs):
        generation = response.generations[0][0]
        text = generation.text
        if text:
            logger.info("chat completion response (%d chars):\n%s\n%s\n%s", len(text), "-" * 60, text, "-" * 60)
            return
        tool_calls = getattr(generation.message, "tool_calls", None)
        if tool_calls:
            logger.info(
                "chat completion response → tool call(s): %s",
                [(call["name"], call["args"]) for call in tool_calls],
            )
        else:
            logger.info("chat completion response (empty)")


def _review_prompt(content: str, instruction: str | None) -> str:
    task = f"Follow this instruction when reviewing the file below: {instruction}" if instruction else (
        "Read the following file and describe any bugs, issues, or improvements you find."
    )
    return f"You are a code reviewer. {task}\nDo not rewrite the file — report your findings as plain text.\n\n{content}"


def _fix_prompt(content: str, instruction: str | None) -> str:
    task = f"Follow this instruction and apply it to the file below: {instruction}" if instruction else (
        "Read the following file, fix any bugs and clear issues, and return the corrected file."
    )
    return (
        f"You are a code fixer. {task}\nReturn ONLY the resulting file content — no explanation, "
        f"no commentary, no markdown code fences.\n\n{content}"
    )


def get_chat_response(message: str) -> str:
    logger.info("chat completion call → model=%s, message_chars=%d", settings.openai_model, len(message))
    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    reply = model.invoke(message).content
    logger.info("chat completion response (%d chars):\n%s\n%s\n%s", len(reply), "-" * 60, reply, "-" * 60)
    return reply


def strip_code_fence(text: str) -> str:
    """Remove a wrapping ```lang ... ``` fence, in case the model adds one anyway."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text


def get_code_response(
    content: str,
    action: Literal["review", "fix"],
    instruction: str | None = None,
) -> str:
    prompt = _review_prompt(content, instruction) if action == "review" else _fix_prompt(content, instruction)
    reply = get_chat_response(prompt)
    return reply if action == "review" else strip_code_fence(reply)
