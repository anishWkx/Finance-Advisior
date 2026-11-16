# Financial Advisor RAG

An AI-powered financial document assistant that uses Retrieval-Augmented Generation (RAG) to answer questions using information extracted from uploaded financial documents.

Instead of relying entirely on an LLM's pretrained knowledge, the application retrieves relevant document passages and generates answers grounded in that context, with source references.

## Features

- **Document Upload:** Upload PDF, CSV and XLSX files (up to 20 MB).
- **PDF Text Extraction:** Extract digital PDF text using PyMuPDF.
- **OCR Processing:** Extract scanned PDF text using Tesseract, with Gemini-powered fallback when OCR quality is poor.
- **Document Chunking:** Split extracted content into smaller sections for retrieval.
- **Semantic Search:** Generate embeddings using Hugging Face Sentence Transformers.
- **Persistent Vector Storage:** Store document embeddings using ChromaDB.
- **AI-Powered Answers:** Generate context-grounded responses using Groq and GPT-OSS-20B.
- **Source References:** Display document names, page numbers and sections supporting answers.
- **Hallucination Control:** Refuse questions when the uploaded documents do not contain sufficient information.
- **Interactive Dashboard:** React-based interface for document uploads and financial question answering.

## Architecture

1. **Frontend:** React and Vite provide the document upload and chat interface.
2. **Backend:** FastAPI handles uploads, document processing and chat requests.
3. **Document Processing:** PyMuPDF extracts digital PDF text, Tesseract handles scanned pages, and Gemini provides OCR fallback. CSV and XLSX files are processed using Pandas.
4. **Chunking:** Extracted document content is divided into smaller text chunks.
5. **Embeddings:** Hugging Face Sentence Transformers (`all-MiniLM-L6-v2`) converts text into 384-dimensional embeddings.
6. **Vector Database:** ChromaDB stores embeddings and document metadata persistently.
7. **Retrieval:** Relevant document passages are retrieved using semantic similarity search.
8. **Generation:** Groq-hosted GPT-OSS-20B generates answers using retrieved context.
9. **Grounding:** The assistant avoids unsupported claims and returns an explicit refusal when the context is insufficient.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite, JavaScript |
| Backend | Python, FastAPI |
| LLM | Groq API, GPT-OSS-20B |
| OCR | Tesseract OCR, Google Gemini |
| Embeddings | Hugging Face Sentence Transformers |
| Vector Database | ChromaDB |
| Document Processing | PyMuPDF, Pandas, Pillow |
| RAG Framework | LangChain integrations |

## Project Structure

```text
financial-advisor-rag/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   ├── rag/
│   │   │   ├── llm_service.py
│   │   │   └── vector_store.py
│   │   ├── services/
│   │   │   ├── chunking.py
│   │   │   ├── document_processor.py
│   │   │   └── handwriting_ocr.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── api.js
│   │   └── main.jsx
│   └── package.json
├── get_embedding_function.py
├── populate_db.py
├── query_data.py
└── README.md
