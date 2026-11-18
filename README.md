# Financial Advisor RAG

An AI-powered financial document assistant that uses Retrieval-Augmented Generation (RAG) to answer questions using information extracted from uploaded financial documents. It retrieves relevant document passages and generates answers grounded in that context, with source references.
 
## Live Demo

- **Frontend:** https://finwise-financial-advisor.vercel.app
- **Backend API:** https://finwise-financial-advisor-api.onrender.com
- **API Documentation:** https://finwise-financial-advisor-api.onrender.com/docs

## Features

- **Secure Authentication:** User registration and login using bcrypt password hashing and JWT authentication.
- **Document Upload:** Upload PDF, CSV, and XLSX files up to 20 MB.
- **PDF Text Extraction:** Extract digital PDF text using PyMuPDF.
- **OCR Processing:** Extract scanned PDF text using Tesseract, with Google Gemini fallback when OCR quality is poor.
- **Document Chunking:** Split extracted content into smaller sections for retrieval.
- **Semantic Search:** Generate embeddings using Hugging Face Sentence Transformers.
- **Persistent Vector Storage:** Store document embeddings using PostgreSQL with PGVector.
- **Persistent File Storage:** Store uploaded documents using Neon Object Storage.
- **AI-Powered Answers:** Generate context-grounded responses using Groq and GPT-OSS-20B.
- **Source References:** Display supporting document names, page numbers, and sections.
- **Hallucination Control:** Refuse questions when uploaded documents do not contain sufficient information.
- **Transaction Extraction:** Extract supported transaction records from compatible bank statement PDFs.
- **Interactive Dashboard:** React-based interface for document uploads, financial questions, and transaction management.

## Architecture

1. **Frontend:** React 19 and Vite provide the user interface.
2. **Backend:** FastAPI handles authentication, uploads, document processing, and chat requests.
3. **Authentication:** JWT-based authentication with bcrypt password hashing.
4. **Database:** Neon PostgreSQL stores user accounts, document metadata, and extracted transactions.
5. **Document Processing:** PyMuPDF extracts digital PDF text, Tesseract handles scanned pages, and Gemini provides OCR fallback. Pandas processes CSV and XLSX files.
6. **Chunking:** Extracted document content is divided into smaller text chunks.
7. **Embeddings:** Hugging Face Sentence Transformers (`all-MiniLM-L6-v2`) generates 384-dimensional embeddings.
8. **Vector Database:** LangChain PGVector stores embeddings and document metadata in PostgreSQL.
9. **Object Storage:** Neon Object Storage stores original uploaded documents through an S3-compatible API.
10. **Retrieval and Generation:** Relevant document passages are retrieved and supplied to Groq-hosted GPT-OSS-20B.
11. **Grounding:** The assistant answers using retrieved document context and refuses unsupported questions.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite, JavaScript, Recharts |
| Backend | Python, FastAPI, Uvicorn |
| Authentication | JWT, bcrypt |
| Database | Neon PostgreSQL |
| Vector Database | PGVector, LangChain PGVector |
| Object Storage | Neon Object Storage, AWS S3-compatible API, Boto3 |
| LLM | Groq API, GPT-OSS-20B |
| OCR | Tesseract OCR, Google Gemini |
| Embeddings | Hugging Face Sentence Transformers |
| Document Processing | PyMuPDF, Pandas, OpenPyXL, Pillow |
| RAG Framework | LangChain integrations |

## Project Structure

```text
financial-advisor-rag/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   └── transactions.py
│   │   ├── auth/
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── rag/
│   │   │   ├── llm_service.py
│   │   │   └── vector_store.py
│   │   ├── services/
│   │   │   ├── chunking.py
│   │   │   ├── document_processor.py
│   │   │   ├── handwriting_ocr.py
│   │   │   └── object_storage.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── api.js
│   │   └── main.jsx
└── README.md
```

## Environment Variables

Configure these variables in your local environment or deployment dashboard. Never commit actual credentials.

### Backend

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `JWT_SECRET` | Secret used to sign authentication tokens |
| `GROQ_API_KEY` | Groq API key for answer generation |
| `GEMINI_API_KEY` | Google Gemini API key for OCR fallback |
| `FRONTEND_URL` | Frontend URL for CORS configuration |
| `AWS_ENDPOINT_URL_S3` | Neon Object Storage S3 endpoint |
| `AWS_ACCESS_KEY_ID` | Object storage access key |
| `AWS_SECRET_ACCESS_KEY` | Object storage secret key |
| `AWS_REGION` | Object storage region |
| `AWS_S3_BUCKET` | Object storage bucket name |

### Frontend

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend |

## Run Locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API documentation:

`http://localhost:8000/docs`

### Frontend

Open a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to `http://localhost:8000` for local development.

## Deployment

The application uses a separate frontend and backend deployment architecture.

- **Frontend:** Vercel (Vite project, root directory: `frontend`).
- **Backend:** Render (FastAPI application).
- **Database:** Neon PostgreSQL with PGVector.
- **File Storage:** Neon Object Storage.

Backend start command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure the environment variables in the respective deployment dashboards. Set `FRONTEND_URL` on Render and `VITE_API_BASE_URL` on Vercel to their corresponding deployed URLs.

## API Documentation

Once the backend is running, access the interactive FastAPI documentation at:

`/docs`
