from pathlib import Path
from uuid import uuid4

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# Store the new vector database inside backend/storage/chroma
BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIR = BASE_DIR / "storage" / "chroma"

COLLECTION_NAME = "financial_documents"

_embedding_function = None
_vector_store = None


def get_embedding_function():
    global _embedding_function

    if _embedding_function is None:
        _embedding_function = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

    return _embedding_function


def get_vector_store():
    global _vector_store

    if _vector_store is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
            persist_directory=str(CHROMA_DIR)
        )

    return _vector_store


def store_chunks(chunks):
    if not chunks:
        return 0

    vector_store = get_vector_store()

    texts = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [str(uuid4()) for _ in chunks]

    vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids
    )

    return len(ids)
