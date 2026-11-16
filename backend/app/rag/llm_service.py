import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from backend/.env")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-20b"

REFUSAL_MESSAGE = (
    "The uploaded document does not contain enough information "
    "to answer this question."
)


def generate_answer(question: str, context: str) -> str:

    system_prompt = """
You are a document-grounded Financial Advisor AI assistant.

Your task is to answer questions using ONLY the supplied document context.

STRICT GROUNDING RULES:

1. Every factual statement must be directly supported by the supplied context.
2. Never use your pretrained knowledge to fill missing information.
3. Never invent examples, benefits, stages, explanations, figures,
   definitions, or financial recommendations.
4. Do not assume that a concept has benefits or characteristics
   unless the document explicitly states them.
5. If the question asks for multiple points but the context supports
   only some of them, provide only the supported points.
6. If the context does not contain enough information to answer,
   return exactly:

   The uploaded document does not contain enough information
   to answer this question.

7. Do not add introductory claims or conclusions that are not
   supported by the document.
8. Explain supported information in simple, student-friendly language.
9. Preserve important financial terminology.
10. Do not mention external knowledge or speculate.

ANSWER FORMAT:

- Use a clear heading when appropriate.
- Use bullet points for explanations.
- Use a table only when the document supports a comparison.
- Avoid repetition.
- Do not add unsupported information to make an answer longer.

Before responding, verify that every factual statement can be traced
to the supplied document context.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Answer strictly using the supplied document context.
"""
            }
        ],
        reasoning_effort="low",
        include_reasoning=False,
        max_completion_tokens=1500
    )

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise ValueError(
            f"Groq returned an empty answer. "
            f"Finish reason: {response.choices[0].finish_reason}"
        )

    return answer.strip()
