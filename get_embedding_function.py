from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
load_dotenv()

def get_embedding_function():
    # embeddings = BedrockEmbeddings(
    #     credentials_profile_name="default", region_name="us-east-1"
    # )
    # embeddings = OllamaEmbeddings(model="nomic-embed-text")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return embeddings

def get_vector_store(use_pinecone=False):
    embedding_function = get_embedding_function()
    
    if use_pinecone:
        # Initialize Pinecone
        from pinecone import Pinecone, ServerlessSpec
        
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = "financial-rag"
        
        # Check if index exists, create if not
        if not pc.has_index(index_name):
            pc.create_index(
                name=index_name,
                dimension=384,  # ← Set to match your local embedding model
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        
        return PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=embedding_function
        )
    else:
        # Use Chroma (default)
        return Chroma(
            persist_directory="chroma",
            embedding_function=embedding_function
        )
