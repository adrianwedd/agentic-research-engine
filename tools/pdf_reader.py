from __future__ import annotations

"""Simple PDF text extraction tool using pdfplumber."""

import io
import os
from urllib.parse import urlparse

import pdfplumber
import requests


def pdf_extract(path_or_url: str, *, timeout: int = 10) -> str:
    """Return the text content of a PDF from ``path_or_url``."""
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

    with pdfplumber.open(file_obj) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    if not text.strip():
        raise ValueError("No extractable text found in PDF")
    return text
