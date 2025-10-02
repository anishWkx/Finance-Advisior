# Financial Advisory RAG System

A retrieval-augmented generation (RAG) system that provides accurate answers to financial questions by retrieving relevant context from embedded financial documents before generating responses.

## Overview

This system combines semantic search with large language models to answer questions about financial concepts. Instead of relying solely on the LLM's training data, it retrieves relevant passages from a knowledge base of financial literature, ensuring responses are grounded in authoritative sources.

## Features

- **Dual Vector Store Support**: Operates with ChromaDB for local development or Pinecone for cloud deployment
- **Semantic Search**: Uses sentence transformers to embed documents and queries for accurate similarity matching
- **Context-Aware Generation**: Retrieves relevant passages before generating responses to improve accuracy

## Architecture

1. **Document Processing**: Financial documents are chunked and embedded using HuggingFace sentence transformers
2. **Vector Storage**: Embeddings are stored in ChromaDB (local) or Pinecone (cloud) for fast similarity search
3. **Query Pipeline**: User questions are embedded and matched against the vector store to retrieve relevant context
4. **Response Generation**: Retrieved context is passed to Llama2 via LangChain to generate accurate, grounded answers
5. **Evaluation**: Automated testing framework validates response accuracy across financial concepts

## Tech Stack

- **LLM**: Llama2
- **Orchestration**: LangChain
- **Vector Databases**: ChromaDB (local), Pinecone (cloud)
- **Embeddings**: HuggingFace Sentence Transformers
- **Language**: Python
