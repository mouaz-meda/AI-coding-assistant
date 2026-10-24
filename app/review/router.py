import logging

from fastapi import APIRouter, Depends

from app.ai.agent import run_agentic_review
from app.ai.errors import translate_ai_errors
from app.ai.llm import get_code_response
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.review.diff import make_diff
from app.schemas.review import (
    MultiReviewRequest,
    MultiReviewResponse,
    ReviewFinding,
    ReviewRequest,
    ReviewResponse,
)

router = APIRouter(tags=["review"])
logger = logging.getLogger(__name__)


@router.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest, current_user: User = Depends(get_current_user)):
    logger.info(
        "POST /review → user=%d, path=%r, action=%s", current_user.id, request.path, request.action
    )
    with translate_ai_errors():
        output = get_code_response(request.content, request.action, request.instruction)
    diff = make_diff(request.path, request.content, output) if request.action == "fix" else None
    logger.info("POST /review → output_chars=%d, diff_chars=%d", len(output), len(diff or ""))
    return ReviewResponse(
        path=request.path,
        action=request.action,
        output=output,
        diff=diff,
        instruction=request.instruction,
    )


@router.post("/review/multi", response_model=MultiReviewResponse)
def review_multi(request: MultiReviewRequest, current_user: User = Depends(get_current_user)):
    logger.info(
        "POST /review/multi → user=%d, files=%d, action=%s", current_user.id, len(request.files), request.action
    )
    with translate_ai_errors():
        result, considered = run_agentic_review(current_user.id, request.files, request.action, request.instruction)
    if request.action == "review":
        findings = [ReviewFinding(path=f.path, notes=f.notes) for f in result.findings]
        logger.info(
            "POST /review/multi → findings=%s, considered=%s", [f.path for f in findings], considered
        )
        return MultiReviewResponse(
            action="review",
            instruction=request.instruction,
            general=result.general or None,
            findings=findings,
            considered_files=considered,
        )

    logger.info("POST /review/multi → edits=%s, considered=%s", [e.path for e in result], considered)
    return MultiReviewResponse(
        action="fix", instruction=request.instruction, edits=result, considered_files=considered
    )
