from __future__ import annotations

"""Simple PDF text extraction tool using pdfplumber."""

import io
import os
from urllib.parse import urlparse

import pdfplumber
import requests
from pdfminer.pdfparser import PDFSyntaxError

from .validation import validate_path_or_url


def pdf_extract(
    path_or_url: str, *, timeout: int = 10, use_ocr: bool | None = None
) -> str:
    """Return the text content of a PDF from ``path_or_url``.

    If ``use_ocr`` is ``True`` and no text is extractable, an OCR attempt will be
    made using ``pytesseract`` if available. If ``use_ocr`` is ``None``, the
    ``PDF_READER_ENABLE_OCR`` environment variable controls the fallback.
    """
    if use_ocr is None:
        env_val = os.getenv("PDF_READER_ENABLE_OCR")
        if env_val is not None:
            use_ocr = env_val.lower() in {"1", "true", "yes"}
        else:
            # auto-enable OCR when pytesseract is importable
            try:
                import importlib

                importlib.import_module("pytesseract")  # type: ignore
                use_ocr = True
            except Exception:
                use_ocr = False
    validated = validate_path_or_url(path_or_url)
    parsed = urlparse(path_or_url)
    if parsed.scheme in {"http", "https"}:
        try:
            resp = requests.get(validated, timeout=timeout)
            resp.raise_for_status()
            file_obj: str | io.BytesIO = io.BytesIO(resp.content)
        except requests.RequestException as exc:  # pragma: no cover - network errors
            raise ValueError(f"Failed to download PDF: {exc}") from exc
    else:
        file_obj = validated

    try:
        with pdfplumber.open(file_obj) as pdf:
            text_parts = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(text_parts)
            if not text.strip() and use_ocr:
                try:  # pragma: no cover - optional OCR path
                    import pytesseract

                    text_parts = []
                    for page in pdf.pages:
                        img = page.to_image(resolution=300).original
                        page_text = pytesseract.image_to_string(img)
                        text_parts.append(page_text)
                    text = "\n".join(text_parts)
                except Exception:  # pragma: no cover - OCR failures
                    use_ocr = False
    except FileNotFoundError as exc:
        raise FileNotFoundError(validated) from exc
    except PDFSyntaxError as exc:
        raise ValueError(f"Invalid PDF: {exc}") from exc
    except Exception as exc:  # pragma: no cover - parsing errors
        msg = str(exc).lower()
        if "password" in msg or "encrypt" in msg:
            raise ValueError("Encrypted PDF: password required") from exc
        raise ValueError(f"Failed to parse PDF: {exc}") from exc

    if not text.strip():
        msg = "No extractable text found in PDF"
        if use_ocr:
            msg += " even with OCR"
        else:
            msg += "; the file may be image-based and require OCR"
        raise ValueError(msg)
    return text
