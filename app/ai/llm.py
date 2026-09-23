from typing import Literal

from openai import OpenAI

from app.config import settings

REVIEW_PROMPT = (
    "You are a code reviewer. Read the following file and describe any bugs, "
    "issues, or improvements you find. Do not rewrite the file — just report "
    "your findings as plain text.\n\n{content}"
)

FIX_PROMPT = (
    "You are a code fixer. Read the following file, fix any bugs and clear "
    "issues, and return the corrected file. Return ONLY the corrected file "
    "content — no explanation, no commentary, no markdown code fences.\n\n{content}"
)


def get_chat_response(message: str) -> str:
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": message}],
    )
    return completion.choices[0].message.content


def strip_code_fence(text: str) -> str:
    """Remove a wrapping ```lang ... ``` fence, in case the model adds one anyway."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text


def get_code_response(content: str, action: Literal["review", "fix"]) -> str:
    prompt_template = REVIEW_PROMPT if action == "review" else FIX_PROMPT
    reply = get_chat_response(prompt_template.format(content=content))
    return reply if action == "review" else strip_code_fence(reply)
