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

INSTRUCTED_REVIEW_PROMPT = (
    "You are a code reviewer. Follow this instruction when reviewing the file below: "
    "{instruction}\n\nDo not rewrite the file — report your findings as plain text.\n\n"
    "File:\n{content}"
)

INSTRUCTED_FIX_PROMPT = (
    "You are a code editor. Follow this instruction and apply it to the file below: "
    "{instruction}\n\nReturn ONLY the resulting file content — no explanation, no "
    "commentary, no markdown code fences.\n\nFile:\n{content}"
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


def get_code_response(
    content: str,
    action: Literal["review", "fix"],
    instruction: str | None = None,
) -> str:
    if instruction:
        prompt_template = INSTRUCTED_REVIEW_PROMPT if action == "review" else INSTRUCTED_FIX_PROMPT
        prompt = prompt_template.format(instruction=instruction, content=content)
    else:
        prompt_template = REVIEW_PROMPT if action == "review" else FIX_PROMPT
        prompt = prompt_template.format(content=content)

    reply = get_chat_response(prompt)
    return reply if action == "review" else strip_code_fence(reply)
