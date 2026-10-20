from fastapi import APIRouter, Depends

from app.ai.agent import run_agentic_review
from app.ai.llm import get_code_response
from app.auth.dependencies import get_current_user
from app.colors import RESET, REVIEW
from app.models.user import User
from app.review.diff import make_diff
from app.schemas.review import MultiReviewRequest, MultiReviewResponse, ReviewRequest, ReviewResponse

router = APIRouter(tags=["review"])


@router.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest, current_user: User = Depends(get_current_user)):
    print(
        f"{REVIEW}[review] POST /review → user={current_user.id}, "
        f"path={request.path!r}, action={request.action}{RESET}"
    )
    output = get_code_response(request.content, request.action, request.instruction)
    diff = make_diff(request.path, request.content, output) if request.action == "fix" else None
    print(f"{REVIEW}[review] POST /review → output_chars={len(output)}, diff_chars={len(diff or '')}{RESET}")
    return ReviewResponse(
        path=request.path,
        action=request.action,
        output=output,
        diff=diff,
        instruction=request.instruction,
    )


@router.post("/review/multi", response_model=MultiReviewResponse)
def review_multi(request: MultiReviewRequest, current_user: User = Depends(get_current_user)):
    print(
        f"{REVIEW}[review] POST /review/multi → user={current_user.id}, "
        f"files={len(request.files)}, action={request.action}{RESET}"
    )
    result, considered = run_agentic_review(current_user.id, request.files, request.action, request.instruction)
    if request.action == "review":
        print(f"{REVIEW}[review] POST /review/multi → considered={considered}{RESET}")
        return MultiReviewResponse(
            action="review", instruction=request.instruction, output=result, considered_files=considered
        )

    print(f"{REVIEW}[review] POST /review/multi → edits={[e.path for e in result]}, considered={considered}{RESET}")
    return MultiReviewResponse(
        action="fix", instruction=request.instruction, edits=result, considered_files=considered
    )
