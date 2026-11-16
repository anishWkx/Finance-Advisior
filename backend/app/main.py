from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router

app = FastAPI(
    title="Financial Advisor RAG",
    description="AI-powered financial document assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Financial Advisor RAG API is running!"}


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Financial Advisor RAG"
    }


app.include_router(documents_router)

from app.api.chat import router as chat_router
app.include_router(chat_router)
