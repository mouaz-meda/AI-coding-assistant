from typing import Literal

from pydantic import BaseModel


class ReviewRequest(BaseModel):
    path: str
    content: str
    action: Literal["review", "fix"]
    instruction: str | None = None


class ReviewResponse(BaseModel):
    path: str
    action: str
    output: str
    diff: str | None = None
    instruction: str | None = None