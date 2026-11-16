from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag.vector_store import get_vector_store
from app.rag.llm_service import generate_answer

router = APIRouter(prefix="/api", tags=["Chat"])

DISTANCE_THRESHOLD = 1.2
RETRIEVAL_COUNT = 10
MAX_CONTEXT_CHUNKS = 5

REFUSAL_MESSAGE = (
    "The uploaded document does not contain enough information "
    "to answer this question."
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        vector_store = get_vector_store()

        results = vector_store.similarity_search_with_score(
            request.question,
            k=RETRIEVAL_COUNT
        )

        unique_documents = []
        seen_content = set()

        for document, distance in results:
            content = document.page_content.strip()

            if distance > DISTANCE_THRESHOLD:
                continue

            if not content or content in seen_content:
                continue

            seen_content.add(content)
            unique_documents.append(document)

            if len(unique_documents) >= MAX_CONTEXT_CHUNKS:
                break

        if not unique_documents:
            return {
                "question": request.question,
                "answer": REFUSAL_MESSAGE,
                "sources": []
            }

        context_parts = []

        for document in unique_documents:
            source = document.metadata.get("source", "Unknown")
            page = document.metadata.get("page", "Unknown")

            context_parts.append(
                f"Source: {source} | Page: {page}\n"
                f"{document.page_content}"
            )

        context = "\n\n".join(context_parts)

        answer = generate_answer(
            question=request.question,
            context=context
        )

        # Return no citations when the LLM refuses to answer.
        if answer.strip() == REFUSAL_MESSAGE:
            return {
                "question": request.question,
                "answer": REFUSAL_MESSAGE,
                "sources": []
            }

        sources = []
        seen_sources = set()

        for document in unique_documents:
            source = document.metadata.get("source", "Unknown")
            page = document.metadata.get("page")
            section = document.metadata.get("section")

            source_key = (source, page, section)

            if source_key not in seen_sources:
                seen_sources.add(source_key)

                sources.append({
                    "source": source,
                    "page": page,
                    "section": section
                })

        return {
            "question": request.question,
            "answer": answer,
            "sources": sources
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(error)}"
        )
