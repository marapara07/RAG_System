from pydantic import BaseModel
from datetime import datetime


class ConversationCreate(BaseModel):
    employee_id: int
    title: str = "New conversation"


class ConversationResponse(BaseModel):
    id: int
    employee_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sources: str | None
    created_at: datetime

    class Config:
        from_attributes = True