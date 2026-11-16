from pathlib import Path
from io import BytesIO
import re
import statistics

import pandas as pd
import pymupdf
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
from pytesseract import Output

from app.services.handwriting_ocr import extract_handwriting


def is_poor_ocr(text: str, confidence: float) -> bool:
    """Check whether Tesseract's extracted text may need better OCR."""
    words = re.findall(r"[A-Za-z]+", text)

    if len(words) < 8 or confidence < 55:
        return True

    words_with_vowels = sum(
        1 for word in words if re.search(r"[aeiou]", word.lower())
    )

    meaningful_ratio = words_with_vowels / len(words)

    return meaningful_ratio < 0.55


def extract_pdf(file_path: Path):
    results = []
    pdf_document = pymupdf.open(str(file_path))

    try:
        for page_number, page in enumerate(pdf_document, start=1):
            # First, try extracting embedded digital PDF text.
            text = page.get_text("text").strip()

            if text:
                results.append({
                    "page": page_number,
                    "content": text
                })
                continue

            # Render scanned pages at a moderate resolution.
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False
            )

            image_bytes = pix.tobytes("png")

            image = Image.open(BytesIO(image_bytes))
            image = ImageOps.grayscale(image)
            image = ImageOps.autocontrast(image)
            image = ImageEnhance.Contrast(image).enhance(1.5)

            # Try traditional OCR first.
            ocr_data = pytesseract.image_to_data(
                image,
                config="--oem 3 --psm 3",
                output_type=Output.DICT
            )

            text = pytesseract.image_to_string(
                image,
                config="--oem 3 --psm 3"
            ).strip()

            confidences = [
                float(value)
                for value in ocr_data["conf"]
                if value not in ("-1", "")
            ]

            average_confidence = (
                statistics.mean(confidences) if confidences else 0
            )

            image.close()

            # Use Gemini only when Tesseract's result looks unreliable.
            if is_poor_ocr(text, average_confidence):
                try:
                    text = extract_handwriting(image_bytes)
                except Exception as error:
                    raise RuntimeError(
                        f"Handwriting OCR failed on PDF page "
                        f"{page_number}: {error}"
                    ) from error

            if text.strip():
                results.append({
                    "page": page_number,
                    "content": text.strip()
                })

    finally:
        pdf_document.close()

    return results


def extract_csv(file_path: Path):
    dataframe = pd.read_csv(file_path)

    if dataframe.empty:
        return []

    return [{
        "sheet": "CSV Data",
        "content": dataframe.to_string(index=False)
    }]


def extract_excel(file_path: Path):
    sheets = pd.read_excel(file_path, sheet_name=None)
    results = []

    for sheet_name, dataframe in sheets.items():
        if dataframe.empty:
            continue

        results.append({
            "sheet": sheet_name,
            "content": dataframe.to_string(index=False)
        })

    return results


def extract_document(file_path: str):
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf(path)

    if extension == ".csv":
        return extract_csv(path)

    if extension == ".xlsx":
        return extract_excel(path)

    raise ValueError(f"Unsupported file type: {extension}")
