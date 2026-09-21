from openai import OpenAI

from app.config import settings


def get_chat_response(message: str) -> str:
    client = OpenAI(api_key=settings.openai_api_key)
    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": message}],
    )
    return completion.choices[0].message.content
