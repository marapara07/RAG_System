from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.connection import engine, Base
from database import models

from routers.chat import router as chat_router
from routers.auth import router as auth_router
from routers.conversations import router as conversations_router
from routers.documents import router as documents_router


app = FastAPI(
    title="AI Helper API",
    description="Backend API for the Retrieval-Augmented Generation chatbot.",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI Helper API is running"
    }


app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(documents_router)
