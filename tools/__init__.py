"""Tool package exposing callable wrappers for external services."""

from .pdf_reader import pdf_extract
from .web_search import web_search

__all__ = ["web_search", "pdf_extract"]
