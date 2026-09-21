from fastapi import APIRouter, Depends

from app.ai.llm import get_chat_response
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    reply = get_chat_response(request.message)
    return ChatResponse(reply=reply)
