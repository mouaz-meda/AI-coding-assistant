from typing import Literal

from pydantic import BaseModel


class ReviewRequest(BaseModel):
    path: str
    content: str
    action: Literal["review", "fix"]


class ReviewResponse(BaseModel):
    path: str
    action: str
    output: str
    diff: str | None = None