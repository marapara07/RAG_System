import gc
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "storage" / "documents"
PERSIST_DIR = BASE_DIR / "chroma_db"

COLLECTION = "docs"
EMBEDDING_MODEL = "nomic-embed-text"


def load_documents():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    docs = []

    txt_files = list(DATA_DIR.glob("**/*.txt"))
    pdf_files = list(DATA_DIR.glob("**/*.pdf"))

    for file_path in txt_files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": file_path.name,
                    "path": str(file_path),
                    "page": None,
                },
            )
        )

    for file_path in pdf_files:
        loader = PyPDFLoader(str(file_path))
        pdf_docs = loader.load()

        for doc in pdf_docs:
            doc.metadata["source"] = file_path.name
            doc.metadata["path"] = str(file_path)

        docs.extend(pdf_docs)

    return docs


def clear_chroma_collection(embeddings):
    """
    Clears the Chroma collection without deleting the chroma_db folder.
    This avoids Windows PermissionError caused by locked Chroma files.
    """
    db = Chroma(
        persist_directory=str(PERSIST_DIR),
        collection_name=COLLECTION,
        embedding_function=embeddings,
    )

    try:
        db.delete_collection()
    except Exception:
        pass

    del db
    gc.collect()


def reindex_documents():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    docs = load_documents()

    if not docs:
        return 0, 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=250,
    )

    chunks = splitter.split_documents(docs)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    clear_chroma_collection(embeddings)

    db = Chroma(
        persist_directory=str(PERSIST_DIR),
        collection_name=COLLECTION,
        embedding_function=embeddings,
    )

    batch_size = 10

    for start in range(0, len(chunks), batch_size):
        end = min(start + batch_size, len(chunks))
        db.add_documents(chunks[start:end])

    try:
        db.persist()
    except Exception:
        pass

    return len(docs), len(chunks)