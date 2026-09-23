from fastapi import APIRouter, Depends

from app.ai.llm import get_code_response
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.review.diff import make_diff
from app.schemas.review import ReviewRequest, ReviewResponse

router = APIRouter(tags=["review"])


@router.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest, current_user: User = Depends(get_current_user)):
    output = get_code_response(request.content, request.action)
    diff = make_diff(request.path, request.content, output) if request.action == "fix" else None
    return ReviewResponse(path=request.path, action=request.action, output=output, diff=diff)
