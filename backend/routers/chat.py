import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Conversation, Message

from schemas.chat_schema import ChatRequest, ChatResponse
from services.rag_service import ask_rag


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == request.conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    user_message = Message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.question,
        sources=None
    )

    db.add(user_message)
    db.commit()

    result = ask_rag(request.question)

    assistant_message = Message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(result["sources"])
    )

    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"]
    )