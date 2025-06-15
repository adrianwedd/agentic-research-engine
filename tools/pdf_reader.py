from __future__ import annotations

"""Simple PDF text extraction tool using pdfplumber."""

import io
import os
from urllib.parse import urlparse

import pdfplumber
import requests
from pdfminer.pdfparser import PDFSyntaxError
from pdfplumber.utils.exceptions import PdfminerException


def pdf_extract(
    path_or_url: str, *, timeout: int = 10, use_ocr: bool | None = None
) -> str:
    """Return the text content of a PDF from ``path_or_url``.

    If ``use_ocr`` is ``True`` and no text is extractable, an OCR attempt will be
    made using ``pytesseract`` if available. If ``use_ocr`` is ``None``, the
    ``PDF_READER_ENABLE_OCR`` environment variable controls the fallback.
    """
    if use_ocr is None:
        use_ocr = os.getenv("PDF_READER_ENABLE_OCR", "false").lower() in {
            "1",
            "true",
            "yes",
        }
    parsed = urlparse(path_or_url)
    if parsed.scheme in {"http", "https"}:
        try:
            resp = requests.get(path_or_url, timeout=timeout)
            resp.raise_for_status()
            file_obj: str | io.BytesIO = io.BytesIO(resp.content)
        except requests.RequestException as exc:  # pragma: no cover - network errors
            raise ValueError(f"Failed to download PDF: {exc}") from exc
    else:
        if not os.path.exists(path_or_url):
            raise FileNotFoundError(path_or_url)
        file_obj = path_or_url

    try:
        with pdfplumber.open(file_obj) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if not page_text.strip() and use_ocr:
                    try:  # pragma: no cover - optional OCR path
                        import pytesseract

                        img = page.to_image(resolution=300).original
                        page_text = pytesseract.image_to_string(img)
                    except Exception as exc:  # pragma: no cover - OCR failures
                        raise ValueError(f"OCR extraction failed: {exc}") from exc
                text_parts.append(page_text)
            text = "\n".join(text_parts)
    except (PDFSyntaxError, PdfminerException) as exc:
        raise ValueError(f"Invalid PDF: {exc}") from exc
    except Exception as exc:  # pragma: no cover - parsing errors
        raise ValueError(f"Failed to parse PDF: {exc}") from exc

    if not text.strip():
        msg = "No extractable text found in PDF"
        if use_ocr:
            msg += " even with OCR"
        else:
            msg += "; the file may be image-based and require OCR"
        raise ValueError(msg)
    return text
