import functools
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

from tools.html_scraper import html_scraper

pytestmark = pytest.mark.core


def _serve_dir(path: Path):
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(path))
    httpd = HTTPServer(("localhost", 0), handler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    return httpd, t


def test_html_scraper_extracts_main_text(tmp_path):
    html = tmp_path / "article.html"
    html.write_text(
        """
        <html>
        <body>
        <header>Header</header>
        <nav>Navigation</nav>
        <article><p>Hello World.</p><p>More text.</p></article>
        <footer>Footer</footer>
        </body>
        </html>
        """,
        encoding="utf-8",
    )
    httpd, t = _serve_dir(tmp_path)
    try:
        url = f"http://localhost:{httpd.server_port}/article.html"
        text = html_scraper(url)
    finally:
        httpd.shutdown()
        t.join()

    assert "Hello World." in text
    assert "More text." in text
    assert "Navigation" not in text


def test_html_scraper_bad_url():
    with pytest.raises(ValueError):
        html_scraper("http://localhost:9/missing", timeout=1)


def test_html_scraper_invalid_scheme():
    with pytest.raises(ValueError):
        html_scraper("javascript:alert(1)")


def test_html_scraper_ftp_scheme():
    with pytest.raises(ValueError):
        html_scraper("ftp://example.com/")


def test_html_scraper_dynamic_content(tmp_path):
    html = tmp_path / "dynamic.html"
    html.write_text(
        """
        <html><head><script>document.body.innerHTML = '<p>Hi</p>';</script></head><body></body></html>
        """,
        encoding="utf-8",
    )
    httpd, t = _serve_dir(tmp_path)
    try:
        url = f"http://localhost:{httpd.server_port}/dynamic.html"
        text = html_scraper(url)
    finally:
        httpd.shutdown()
        t.join()

    assert "Hi" in text


def test_html_scraper_traversal(tmp_path):
    path = tmp_path / ".." / "etc" / "passwd.html"
    with pytest.raises(ValueError):
        html_scraper(f"file://{path}")
