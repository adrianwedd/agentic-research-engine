import base64
import functools
import shutil
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from tools.pdf_reader import pdf_extract

HELLO_PDF_B64 = (
    "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2Jq"
    "CjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9Db3VudCAxIC9LaWRzIFszIDAgUl0gPj4KZW5kb2Jq"
    "CjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAyMDAg"
    "MjAwXSAvQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAvRjEgNSAwIFIgPj4g"
    "Pj4gPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA0NCA+PgpzdHJlYW0KQlQKL0YxIDI0IFRm"
    "CjUwIDE1MCBUZAooSGVsbG8gUERGKSBUagpFVAplbmRzdHJlYW0KZW5kb2JqCjUgMCBvYmoKPDwg"
    "L1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9udCAvSGVsdmV0aWNhID4+CmVuZG9i"
    "agp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTAgMDAwMDAgbiAKMDAwMDAw"
    "MDA1MyAwMDAwMCBuIAowMDAwMDAwMTA4IDAwMDAwIG4gCjAwMDAwMDAyMTggMDAwMDAgbiAKMDAw"
    "MDAwMDMwMiAwMDAwMCBuIAp0cmFpbGVyCjw8IC9Sb290IDEgMCBSIC9TaXplIDYgPj4Kc3RhcnR4"
    "cmVmCjM2OAolJUVPRg=="
)

BLANK_PDF_B64 = (
    "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2Jq"
    "CjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9Db3VudCAxIC9LaWRzIFszIDAgUl0gPj4KZW5kb2Jq"
    "CjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAyMDAg"
    "MjAwXSAvQ29udGVudHMgNCAwIFIgPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCAwID4+CnN0"
    "cmVhbQoKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAw"
    "MDAwMTAgMDAwMDAgbiAKMDAwMDAwMDA1MyAwMDAwMCBuIAowMDAwMDAwMTA4IDAwMDAwIG4gCjAw"
    "MDAwMDAyMDMgMDAwMDAgbiAKdHJhaWxlcgo8PCAvUm9vdCAxIDAgUiAvU2l6ZSA1ID4+CnN0YXJ0"
    "eHJlZgoyMzIKJSVFT0Y="
)


def _serve_dir(path: Path):
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(path))
    httpd = HTTPServer(("localhost", 0), handler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    return httpd, t


def _make_scanned_pdf(path: Path, text: str = "OCR TEST") -> None:
    img = Image.new("RGB", (200, 100), "white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), text, fill="black", font=ImageFont.load_default())
    img.save(path, "PDF")


def test_pdf_extract_from_url(tmp_path):
    pdf_path = tmp_path / "hello.pdf"
    pdf_path.write_bytes(base64.b64decode(HELLO_PDF_B64))
    httpd, t = _serve_dir(tmp_path)
    try:
        url = f"http://localhost:{httpd.server_port}/hello.pdf"
        text = pdf_extract(url)
    finally:
        httpd.shutdown()
        t.join()
    assert "Hello PDF" in text


def test_pdf_extract_no_text(tmp_path):
    blank = tmp_path / "blank.pdf"
    blank.write_bytes(base64.b64decode(BLANK_PDF_B64))
    with pytest.raises(ValueError) as exc:
        pdf_extract(str(blank))
    assert "image-based" in str(exc.value)


def test_pdf_extract_scanned_with_ocr(tmp_path):
    pytest.importorskip("pytesseract")
    if shutil.which("tesseract") is None:
        pytest.skip("tesseract not installed")
    scan = tmp_path / "scan.pdf"
    _make_scanned_pdf(scan, "HELLO OCR")
    text = pdf_extract(str(scan), use_ocr=True)
    assert "HELLO" in text


def test_pdf_extract_bad_path():
    with pytest.raises(FileNotFoundError):
        pdf_extract("/no/such/file.pdf")


def test_pdf_extract_invalid_pdf(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_text("not a pdf")
    with pytest.raises(ValueError) as exc:
        pdf_extract(str(bad))
    assert "Invalid PDF" in str(exc.value)


def test_pdf_extract_bad_url():
    with pytest.raises(ValueError) as exc:
        pdf_extract("http://localhost:9/missing.pdf", timeout=1)
    assert "Failed to download PDF" in str(exc.value)
