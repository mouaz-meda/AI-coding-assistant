from typing import Literal

from pydantic import BaseModel

from app.schemas.ingestion import ProjectFile


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


class MultiReviewRequest(BaseModel):
    files: list[ProjectFile]
    action: Literal["review", "fix"]
    instruction: str


class FileEdit(BaseModel):
    path: str
    output: str
    diff: str


class MultiReviewResponse(BaseModel):
    action: str
    instruction: str
    output: str | None = None
    edits: list[FileEdit] = []