from pathlib import Path
import re
import ollama

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


BASE_DIR = Path(__file__).resolve().parents[1]

PERSIST_DIR = BASE_DIR / "chroma_db"
COLLECTION = "docs"

LLM_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"


def load_vector_db():
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    return Chroma(
        persist_directory=str(PERSIST_DIR),
        collection_name=COLLECTION,
        embedding_function=embeddings,
    )


def build_history_text(chat_history=None):
    if not chat_history:
        return ""

    lines = []

    for msg in chat_history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


def is_general_question(question: str):
    q = question.lower().strip()

    general_patterns = [
        r"^(salut|hello|hi|hey|bonjour|buna|bună)$",
        r"ce faci",
        r"cum esti",
        r"cum ești",
        r"esti acolo",
        r"ești acolo",
        r"romana stii",
        r"știi română",
        r"stii romana",
        r"vorbesti romana",
        r"vorbești română",
        r"do you speak",
        r"can you speak",
        r"who are you",
        r"cine esti",
        r"cine ești",
    ]

    return any(re.search(pattern, q) for pattern in general_patterns)


def answer_general_question(question: str, chat_history=None):
    history_text = build_history_text(chat_history)

    prompt = f"""
You are a natural multilingual assistant.

Answer in the same language as the user's latest message.
If the user writes in Romanian, answer in Romanian.
If the user writes in English, answer in English.
If the user writes in French, answer in French.

Be brief, natural, and friendly.
Do not mention documents or sources.

Conversation history:
{history_text}

User message:
{question}

Answer:
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a natural multilingual assistant. Always answer in the language of the user's latest message.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        options={
            "temperature": 0.4,
            "num_ctx": 2048,
            "num_batch": 32,
            "num_gpu": 0,
        },
    )

    return {
        "answer": response["message"]["content"],
        "sources": [],
    }


def get_all_sources_from_db(db):
    try:
        data = db.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])

        sources = sorted(
            set(
                metadata.get("source")
                for metadata in metadatas
                if metadata and metadata.get("source")
            )
        )

        return sources
    except Exception:
        return []


def find_mentioned_source(question: str, available_sources):
    q = question.lower()

    for source in available_sources:
        source_lower = source.lower()
        stem = Path(source_lower).stem

        if source_lower in q or stem in q:
            return source

    return None


def get_docs_by_source(db, source_name: str, max_docs=6):
    try:
        data = db.get(
            where={"source": source_name},
            include=["documents", "metadatas"],
        )

        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        docs = []

        for content, metadata in zip(documents, metadatas):
            docs.append(
                Document(
                    page_content=content,
                    metadata=metadata or {},
                )
            )

        return docs[:max_docs]

    except Exception:
        return []


def retrieve_docs(db, question: str, chat_history=None):
    available_sources = get_all_sources_from_db(db)
    mentioned_source = find_mentioned_source(question, available_sources)

    if mentioned_source:
        docs = get_docs_by_source(db, mentioned_source)

        if docs:
            return docs

    history_text = build_history_text(chat_history)

    retrieval_query = f"""
Conversation history:
{history_text}

Current question:
{question}
"""

    retrieved_docs = db.max_marginal_relevance_search(
        retrieval_query,
        k=5,
        fetch_k=20,
    )

    return retrieved_docs


def select_context_docs(retrieved_docs, max_docs=4):
    if not retrieved_docs:
        return []

    main_source = retrieved_docs[0].metadata.get("source", "?")

    selected_docs = [
        doc for doc in retrieved_docs
        if doc.metadata.get("source", "?") == main_source
    ]

    if selected_docs:
        return selected_docs[:max_docs]

    return retrieved_docs[:max_docs]


def build_prompt(question: str, retrieved_docs, chat_history=None):
    context_blocks = []

    for i, doc in enumerate(retrieved_docs, start=1):
        source = doc.metadata.get("source", "?")
        page = doc.metadata.get("page", None)

        source_line = source
        if page is not None:
            source_line += f" (page {page})"

        context_blocks.append(
            f"[{i}] Source: {source_line}\nContent:\n{doc.page_content}"
        )

    context = "\n\n".join(context_blocks)
    history_text = build_history_text(chat_history)

    return f"""
You are an intelligent assistant for regulatory and audit support.

Language rule:
Answer strictly in the same language as the user's latest question.
If the user asks in Romanian, answer in Romanian.
If the user asks in English, answer in English.
If the user asks in French, answer in French.

Style rule:
Answer naturally, clearly, and professionally.
Do not sound robotic.
Do not start with "Based on the context" unless it is really necessary.
Do not ask for clarification if the retrieved context already contains the answer.

Conversation rule:
Use the conversation history to understand references to previous topics, names, documents, or entities.

Knowledge rule:
Use the retrieved context as the factual source.
If the answer exists in the context, answer directly.
If the context is incomplete, answer only with what is available.

Source rule:
Do not list document names inside the answer.
The application displays sources separately.

Conversation history:
{history_text}

User question:
{question}

Retrieved context:
{context}

Answer:
"""


def get_sources(retrieved_docs):
    sources = []

    for doc in retrieved_docs:
        source = doc.metadata.get("source", "?")

        if source not in sources:
            sources.append(source)

    return sources


def ask_rag(question: str, chat_history=None):
    if is_general_question(question):
        return answer_general_question(question, chat_history)

    db = load_vector_db()

    retrieved_docs = retrieve_docs(db, question, chat_history)

    if not retrieved_docs:
        return {
            "answer": "Nu am găsit suficiente informații în documentele disponibile pentru a răspunde la această întrebare.",
            "sources": [],
        }

    context_docs = select_context_docs(retrieved_docs)

    prompt = build_prompt(question, context_docs, chat_history)

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an intelligent multilingual assistant.
Always answer in the same language as the user's latest question.
Use the retrieved context as the factual source.
Do not mention sources inside the answer.
""",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        options={
            "temperature": 0.3,
            "num_ctx": 4096,
            "num_batch": 32,
            "num_gpu": 0,
        },
    )

    return {
        "answer": response["message"]["content"],
        "sources": get_sources(context_docs),
    }