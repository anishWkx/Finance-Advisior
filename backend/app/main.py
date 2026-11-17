import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router
from app.api.transactions import router as transactions_router
from app.auth.database import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Financial Advisor RAG",
    description="AI-powered financial document assistant",
    version="1.0.0",
    lifespan=lifespan,
)

frontend_urls = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

allowed_origins = [
    url.strip().rstrip("/")
    for url in frontend_urls.split(",")
    if url.strip()
]

for origin in (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
):
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
        "application": "Financial Advisor RAG",
    }


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(transactions_router)
