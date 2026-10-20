from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.colors import INGEST, RESET
from app.config import settings
from app.ingestion.loader import (
    FileRejectedError,
    IngestResult,
    PathNotAllowedError,
    TooManyFilesError,
    filter_files,
    load_directory,
    read_file,
    resolve_within_root,
)
from app.models.user import User
from app.schemas.ingestion import (
    AcceptedFile,
    IngestSummary,
    PathFileRequest,
    PathRequest,
    ProjectFile,
    UploadRequest,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


def to_summary(result: IngestResult) -> IngestSummary:
    accepted = [AcceptedFile(path=f.path, size=len(f.content.encode("utf-8"))) for f in result.accepted]
    return IngestSummary(
        accepted=accepted,
        skipped=result.skipped,
        total_accepted=len(accepted),
        total_skipped=len(result.skipped),
    )


@router.post("/upload", response_model=IngestSummary)
def ingest_upload(request: UploadRequest, current_user: User = Depends(get_current_user)):
    print(f"{INGEST}[ingest] POST /ingest/upload → user={current_user.id}, files={len(request.files)}{RESET}")
    try:
        result = filter_files(request.files)
    except TooManyFilesError as error:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(error))
    summary = to_summary(result)
    print(f"{INGEST}[ingest] POST /ingest/upload → accepted={summary.total_accepted}, skipped={summary.total_skipped}{RESET}")
    return summary


@router.post("/path", response_model=IngestSummary)
def ingest_path(request: PathRequest, current_user: User = Depends(get_current_user)):
    print(f"{INGEST}[ingest] POST /ingest/path → user={current_user.id}, path={request.path!r}{RESET}")
    if not settings.ingest_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server-side path ingestion is disabled (INGEST_ROOT is not set)",
        )

    try:
        directory = resolve_within_root(settings.ingest_root, request.path)
    except PathNotAllowedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))

    if not directory.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a directory")

    try:
        result = load_directory(directory)
    except TooManyFilesError as error:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(error))
    summary = to_summary(result)
    print(f"{INGEST}[ingest] POST /ingest/path → accepted={summary.total_accepted}, skipped={summary.total_skipped}{RESET}")
    return summary


@router.post("/path/file", response_model=ProjectFile)
def ingest_path_file(request: PathFileRequest, current_user: User = Depends(get_current_user)):
    print(
        f"{INGEST}[ingest] POST /ingest/path/file → user={current_user.id}, "
        f"path={request.path!r}, file={request.file!r}{RESET}"
    )
    if not settings.ingest_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server-side path ingestion is disabled (INGEST_ROOT is not set)",
        )

    try:
        directory = resolve_within_root(settings.ingest_root, request.path)
        file = read_file(directory, request.file)
        print(f"{INGEST}[ingest] POST /ingest/path/file → {len(file.content)} chars{RESET}")
        return file
    except PathNotAllowedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    except FileRejectedError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File not usable: {error}")
