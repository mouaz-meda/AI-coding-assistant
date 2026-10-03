from pydantic import BaseModel


class ProjectFile(BaseModel):
    path: str
    content: str


class UploadRequest(BaseModel):
    files: list[ProjectFile]


class PathRequest(BaseModel):
    path: str


class PathFileRequest(BaseModel):
    path: str
    file: str


class AcceptedFile(BaseModel):
    path: str
    size: int


class SkippedFile(BaseModel):
    path: str
    reason: str


class IngestSummary(BaseModel):
    accepted: list[AcceptedFile]
    skipped: list[SkippedFile]
    total_accepted: int
    total_skipped: int
