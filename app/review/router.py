from fastapi import APIRouter, Depends

from app.ai.llm import get_code_response, get_multi_file_response
from app.ai.retrieval import select_relevant_files
from app.auth.dependencies import get_current_user
from app.config import settings
from app.models.user import User
from app.review.diff import make_diff
from app.review.multi import parse_file_edits
from app.schemas.review import MultiReviewRequest, MultiReviewResponse, ReviewRequest, ReviewResponse

router = APIRouter(tags=["review"])


@router.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest, current_user: User = Depends(get_current_user)):
    output = get_code_response(request.content, request.action, request.instruction)
    diff = make_diff(request.path, request.content, output) if request.action == "fix" else None
    return ReviewResponse(
        path=request.path,
        action=request.action,
        output=output,
        diff=diff,
        instruction=request.instruction,
    )


@router.post("/review/multi", response_model=MultiReviewResponse)
def review_multi(request: MultiReviewRequest, current_user: User = Depends(get_current_user)):
    if len(request.files) > settings.rag_top_files:
        files = select_relevant_files(request.files, request.instruction)
    else:
        files = request.files
    considered = [f.path for f in files]

    reply = get_multi_file_response(files, request.action, request.instruction)
    if request.action == "review":
        return MultiReviewResponse(
            action="review", instruction=request.instruction, output=reply, considered_files=considered
        )

    originals = {f.path: f.content for f in files}
    edits = parse_file_edits(reply, originals)
    return MultiReviewResponse(
        action="fix", instruction=request.instruction, edits=edits, considered_files=considered
    )
