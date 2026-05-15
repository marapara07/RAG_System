from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    filename: str
    path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ReindexResponse(BaseModel):
    documents_count: int
    chunks_count: int
    message: str