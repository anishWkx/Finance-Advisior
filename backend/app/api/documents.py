
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
)

from app.auth.security import get_current_user
from app.auth.database import (
    save_document,
    save_transactions,
    get_user_documents,
)
from app.services.document_processor import extract_document
from app.services.transaction_extractor import (
    extract_us_statement_transactions,
    extract_generic_statement_transactions,
)
from app.services.chunking import chunk_document
from app.rag.vector_store import store_chunks
from app.services.object_storage import (
    upload_document as upload_to_storage,
    delete_document as delete_from_storage,
)


router = APIRouter(prefix="/api/documents", tags=["Documents"])

BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx"}

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@router.get("/")
async def list_documents(
    current_user: dict = Depends(get_current_user),
):
    documents = get_user_documents(current_user["id"])

    return {
        "documents": [
            {
                "document_id": document["id"],
                "name": document["original_filename"],
                "file_type": document["file_type"],
                "file_size_bytes": document["file_size_bytes"],
                "chunk_count": document["chunk_count"],
                "created_at": document["created_at"],
            }
            for document in documents
        ]
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, CSV and XLSX files are supported",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="File is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be less than 20 MB",
        )

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    if extension == ".xlsx" and not content.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail="Invalid Excel file",
        )

    unique_filename = f"{uuid4().hex}{extension}"
    document_id = uuid4().hex

    object_key = (
        f"users/{current_user['id']}/documents/{unique_filename}"
    )

    file_path = UPLOAD_DIR / unique_filename
    file_path.write_bytes(content)

    storage_uploaded = False

    try:
        # 1. Extract document text.
        extracted_data = extract_document(str(file_path))

        total_characters = sum(
            len(item.get("content", ""))
            for item in extracted_data
        )

        if total_characters == 0:
            raise HTTPException(
                status_code=422,
                detail="No readable text found in document",
            )

        # 2. Generate RAG chunks.
        chunks = chunk_document(
            extracted_data,
            file.filename,
            extension.replace(".", "").upper(),
        )

        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="Could not generate text chunks",
            )

        # 3. Associate chunks with the authenticated user.
        for chunk in chunks:
            chunk["metadata"]["user_id"] = current_user["id"]

        # 4. Extract transactions.
        transactions = []

        if extension == ".pdf":
            combined_text = "\n".join(
                section.get("content", "")
                for section in extracted_data
            )

            is_us_bank_statement = (
                "Account Transactions by date" in combined_text
                and "Beginning balance" in combined_text
            )

            if is_us_bank_statement:
                transactions = extract_us_statement_transactions(
                    extracted_data
                )
            else:
                transactions = extract_generic_statement_transactions(
                    extracted_data
                )

        # 5. Attach document and user IDs.
        for transaction in transactions:
            transaction["document_id"] = document_id
            transaction["user_id"] = current_user["id"]

        extracted_count = len(transactions)

        print(f"DEBUG: Extracted transactions: {extracted_count}")

        if transactions:
            print("DEBUG: First transaction:", transactions[0])
            print("DEBUG: Last transaction:", transactions[-1])

        # 6. Store original file.
        upload_to_storage(
            content=content,
            object_key=object_key,
            content_type=CONTENT_TYPES[extension],
        )
        storage_uploaded = True

        # 7. Store RAG chunks.
        stored_chunks = store_chunks(chunks)

        # 8. Save document metadata.
        save_document(
            document_id=document_id,
            user_id=current_user["id"],
            original_filename=file.filename,
            stored_filename=object_key,
            file_type=extension.replace(".", "").upper(),
            file_size_bytes=len(content),
            chunk_count=stored_chunks,
        )

        # 9. Save ALL extracted transactions.
        saved_transactions = save_transactions(transactions)

        print(f"DEBUG: Transactions saved: {saved_transactions}")

        if saved_transactions != extracted_count:
            raise RuntimeError(
                f"Transaction count mismatch: "
                f"{extracted_count} extracted, "
                f"{saved_transactions} saved"
            )

    except HTTPException:
        if storage_uploaded:
            try:
                delete_from_storage(object_key)
            except Exception:
                pass
        raise

    except Exception as error:
        if storage_uploaded:
            try:
                delete_from_storage(object_key)
            except Exception:
                pass

        raise HTTPException(
            status_code=422,
            detail=f"Could not process document: {str(error)}",
        ) from error

    finally:
        file_path.unlink(missing_ok=True)

    return {
        "message": "Document uploaded and stored successfully",
        "document_id": document_id,
        "original_filename": file.filename,
        "saved_filename": object_key,
        "file_type": extension.replace(".", "").upper(),
        "file_size": len(content),
        "extracted_sections": len(extracted_data),
        "total_characters": total_characters,
        "total_chunks": len(chunks),
        "stored_chunks": stored_chunks,
        "extracted_transactions": extracted_count,
        "saved_transactions": saved_transactions,
        "storage": "Neon Object Storage",
    }
