from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from app.auth.database import DATABASE_URL

COLLECTION_NAME = "financial_documents"
EMBEDDING_LENGTH = 384

_embedding_function = None
_vector_store = None


def get_embedding_function():
    global _embedding_function

    if _embedding_function is None:
        _embedding_function = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embedding_function


def get_vector_store():
    global _vector_store

    if _vector_store is None:
        _vector_store = PGVector(
            embeddings=get_embedding_function(),
            collection_name=COLLECTION_NAME,
            connection=DATABASE_URL,
            embedding_length=EMBEDDING_LENGTH,
            create_extension=False,
            use_jsonb=True,
        )

    return _vector_store


def store_chunks(chunks):
    if not chunks:
        return 0

    vector_store = get_vector_store()

    texts = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
    )

    return len(texts)
