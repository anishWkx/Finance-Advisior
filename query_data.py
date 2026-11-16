import argparse
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from get_embedding_function import get_vector_store

PROMPT_TEMPLATE = """

You are an expert in financial advice and have read all of the most popular books on finance.
Assume that the person asking the question is a beginner investor looking for clear, concise, and practical advice.
Keep your answers brief (1-2 sentences) and to the point.
Answer the question based on the following context:

{context}

---

Answer the question based on the above context in 1-2 concise sentences: {question}
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    parser.add_argument(
        "--pinecone",
        action="store_true",
        help="Use Pinecone instead of Chroma."
    )

    args = parser.parse_args()

    query_text = args.query_text
    query_rag(query_text, use_pinecone=args.pinecone)


def query_rag(query_text: str, use_pinecone=False):

    print(f"🔍 Using {'Pinecone' if use_pinecone else 'Chroma'} for search...")

    db = get_vector_store(use_pinecone)

    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join(
        [doc.page_content for doc, _score in results]
    )

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(
        context=context_text,
        question=query_text
    )

    model = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )

    response = model.invoke(prompt)
    response_text = response.content

    sources = [
        doc.metadata.get("id", None)
        for doc, _score in results
    ]

    formatted_response = f"Response: {response_text}\nSources: {sources}"

    print(formatted_response)

    return response_text


if __name__ == "__main__":
    main()
