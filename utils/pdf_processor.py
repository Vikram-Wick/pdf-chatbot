import re
from typing import List, Dict

import pdfplumber

try:
    from PyPDF2 import PdfReader  # fallback
except Exception:
    PdfReader = None


def _clean_text(text: str) -> str:
    if not text:
        return ""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_by_page(file_path: str) -> List[Dict]:
    pages: List[Dict] = []

    # Prefer pdfplumber for richer extraction
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                txt = page.extract_text() or ""
                pages.append({"page": i, "text": _clean_text(txt), "source": file_path.split("/")[-1]})
        return pages
    except Exception:
        pass

    # Fallback to PyPDF2 if pdfplumber fails
    if PdfReader is not None:
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages, start=1):
                txt = page.extract_text() or ""
                pages.append({"page": i, "text": _clean_text(txt), "source": file_path.split("/")[-1]})
            return pages
        except Exception:
            pass

    # If both fail, return empty list to let caller handle
    return pages
