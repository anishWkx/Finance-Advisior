import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from backend/.env")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.1-flash-lite"

MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]


def is_temporary_error(error: Exception) -> bool:
    """Identify temporary Gemini API errors that are safe to retry."""

    code = getattr(error, "code", None)
    status = getattr(error, "status", None)

    error_details = (
        f"{code} {status} {str(error)}"
    ).upper()

    temporary_indicators = [
        "429",
        "500",
        "502",
        "503",
        "504",
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "INTERNAL",
        "DEADLINE_EXCEEDED",
        "TOO MANY REQUESTS",
    ]

    return any(
        indicator in error_details
        for indicator in temporary_indicators
    )


def extract_handwriting(image_bytes: bytes) -> str:
    prompt = """
    You are an accurate handwriting transcription system.

    Read the ENTIRE handwritten page from top to bottom.

    Requirements:
    1. Transcribe every visible word on the page.
    2. Do not summarize, shorten, or omit any content.
    3. Preserve headings, questions, numbering, bullets and paragraphs.
    4. Continue reading until the physical bottom of the page.
    5. Preserve financial terminology, examples and explanations.
    6. If a word is unclear, write [unclear].
    7. Do not complete sentences using guesses.
    8. Do not stop after the first section or paragraph.
    9. Return the complete transcription only.

    Check that you have covered the entire page before responding.
    """

    for attempt in range(MAX_RETRIES + 1):
        try:
            print(
                f"Gemini OCR attempt {attempt + 1}/{MAX_RETRIES + 1}..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png"
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4096
                )
            )

            if not response.text or not response.text.strip():
                raise ValueError("Gemini returned empty OCR text.")

            if response.candidates:
                print(
                    "Gemini finish reason:",
                    response.candidates[0].finish_reason
                )

            print("Gemini usage:", response.usage_metadata)

            return response.text.strip()

        except Exception as error:
            if attempt >= MAX_RETRIES or not is_temporary_error(error):
                raise

            delay = RETRY_DELAYS[attempt]

            print(
                f"Temporary Gemini OCR error: {error}. "
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError("Gemini OCR failed after all retry attempts.")
