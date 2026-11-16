from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.document_processor import extract_document
from app.services.chunking import chunk_document
from app.rag.vector_store import store_chunks

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, CSV and XLSX files are supported"
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be less than 20 MB"
        )

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    if extension == ".xlsx" and not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Invalid Excel file")

    unique_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / unique_filename

    file_path.write_bytes(content)

    try:
        extracted_data = extract_document(str(file_path))

        total_characters = sum(
            len(item.get("content", "")) for item in extracted_data
        )

        if total_characters == 0:
            raise HTTPException(
                status_code=422,
                detail="No readable text found in document"
            )

        chunks = chunk_document(
            extracted_data,
            file.filename,
            extension.replace(".", "").upper()
        )

        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="Could not generate text chunks"
            )

        stored_chunks = store_chunks(chunks)

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except Exception as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=f"Could not process document: {str(error)}"
        )

    return {
        "message": "Document uploaded and stored successfully",
        "original_filename": file.filename,
        "saved_filename": unique_filename,
        "file_type": extension.replace(".", "").upper(),
        "file_size": len(content),
        "extracted_sections": len(extracted_data),
        "total_characters": total_characters,
        "total_chunks": len(chunks),
        "stored_chunks": stored_chunks
    }
