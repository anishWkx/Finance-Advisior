import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function, get_vector_store

CHROMA_PATH = "chroma"
DATA_PATH = "data"

def main():
    # Check if the database should be cleared and which vector store to use
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    parser.add_argument("--pinecone", action="store_true", help="Use Pinecone instead of Chroma.")
    args = parser.parse_args()
    
    if args.reset:
        print("✨ Clearing Database")
        clear_database(use_pinecone=args.pinecone)

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_vector_store(chunks, use_pinecone=args.pinecone)

def load_documents():
    # Debug: Process each PDF individually to find the problematic one
    import os
    from langchain_community.document_loaders import PyPDFLoader
    
    pdf_files = [f for f in os.listdir(DATA_PATH) if f.endswith('.pdf')]
    print(f"Found PDF files: {pdf_files}")
    
    all_documents = []
    
    for pdf_file in pdf_files:
        file_path = os.path.join(DATA_PATH, pdf_file)
        print(f"Processing: {pdf_file}")
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            all_documents.extend(documents)
            print(f"✅ Successfully loaded: {pdf_file} ({len(documents)} pages)")
        except Exception as e:
            print(f"❌ Failed to load: {pdf_file}")
            print(f"Error: {str(e)}")
            print("Skipping this file...\n")
            continue
    
    print(f"Total documents loaded: {len(all_documents)}")
    return all_documents

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_vector_store(chunks: list[Document], use_pinecone=False):
    # Load the vector store
    db = get_vector_store(use_pinecone)
    
    if use_pinecone:
        # For Pinecone, add all chunks (it handles duplicates internally)
        chunks_with_ids = calculate_chunk_ids(chunks)
        print(f"👉 Adding documents to Pinecone: {len(chunks_with_ids)}")
        
        # Add documents with their IDs as metadata
        db.add_documents(chunks_with_ids)
        
    else:
        # For Chroma, check for existing documents to avoid duplicates
        chunks_with_ids = calculate_chunk_ids(chunks)
        existing_items = db.get(include=[])
        existing_ids = set(existing_items["ids"])
        print(f"Number of existing documents in DB: {len(existing_ids)}")

        new_chunks = []
        for chunk in chunks_with_ids:
            if chunk.metadata["id"] not in existing_ids:
                new_chunks.append(chunk)

        if len(new_chunks):
            print(f"👉 Adding new documents: {len(new_chunks)}")
            new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
            db.add_documents(new_chunks, ids=new_chunk_ids)
        else:
            print("✅ No new documents to add")

def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks

def clear_database(use_pinecone=False):
    if use_pinecone:
        # For Pinecone, delete all vectors from the index
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("financial-rag")
        index.delete(delete_all=True)
        print("Cleared Pinecone index")
    else:
        # For Chroma, remove the directory
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
            print("Cleared Chroma database")

if __name__ == "__main__":
    main()