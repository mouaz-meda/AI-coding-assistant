from typing import Literal

from openai import OpenAI

from app.colors import LLM, RESET
from app.config import settings

# Delimiter the model's fix-mode reply uses to mark a file boundary — a plain
# text marker avoids the escaping headaches of asking the model to return code
# inside JSON. Shared with app/ai/agent.py's system prompt and
# app/review/multi.py's parser.
FILE_MARKER = "=== {path} ==="


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
    print(f"{LLM}[llm] chat completion call → model={settings.openai_model}, message_chars={len(message)}{RESET}")
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": message}],
    )
    reply = completion.choices[0].message.content
    print(f"{LLM}[llm] chat completion response ({len(reply)} chars):\n{'-' * 60}\n{reply}\n{'-' * 60}{RESET}")
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
