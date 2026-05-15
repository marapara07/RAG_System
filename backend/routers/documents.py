from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Document

from schemas.document_schema import DocumentResponse, ReindexResponse
from services.document_service import reindex_documents


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "storage" / "documents"

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are allowed.",
        )

    save_path = DATA_DIR / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(
        filename=file.filename,
        path=str(save_path),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db),
):
    return db.query(Document).order_by(
        Document.uploaded_at.desc()
    ).all()


@router.post("/reindex", response_model=ReindexResponse)
def reindex():
    docs_count, chunks_count = reindex_documents()

    return ReindexResponse(
        documents_count=docs_count,
        chunks_count=chunks_count,
        message="Documents reindexed successfully.",
    )