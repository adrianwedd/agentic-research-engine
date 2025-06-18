from __future__ import annotations

"""Simple PDF text extraction tool using pdfplumber."""

import io
import os
import time
from urllib.parse import urlparse

import pdfplumber
import requests
from pdfminer.pdfparser import PDFSyntaxError

from .validation import validate_path_or_url


def pdf_extract(
    path_or_url: str,
    *,
    timeout: int = 10,
    use_ocr: bool | None = None,
    retries: int = 2,
    backoff: float = 1.0,
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
        file_obj: str | io.BytesIO | None = None
        for attempt in range(retries + 1):
            try:
                resp = requests.get(validated, timeout=timeout)
                resp.raise_for_status()
                file_obj = io.BytesIO(resp.content)
                break
            except (
                requests.RequestException
            ) as exc:  # pragma: no cover - network errors
                if attempt >= retries:
                    raise ValueError(f"Failed to download PDF: {exc}") from exc
                time.sleep(backoff * 2**attempt)
        if file_obj is None:
            raise ValueError("Failed to download PDF")
    else:
        file_obj = validated

    try:
        with pdfplumber.open(file_obj) as pdf:
            text_parts: list[str] = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if not page_text and use_ocr:
                    try:  # pragma: no cover - optional OCR path
                        import pytesseract

                        img = page.to_image(resolution=300).original
                        page_text = pytesseract.image_to_string(img)
                    except Exception:  # pragma: no cover - OCR failures
                        page_text = ""
                        use_ocr = False
                text_parts.append(page_text or "")
            text = "\n".join(text_parts)
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
