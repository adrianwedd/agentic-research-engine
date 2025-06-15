"""Tool package exposing callable wrappers for external services."""

from . import web_search
from .html_scraper import html_scraper
from .ltm_client import consolidate_memory, retrieve_memory
from .pdf_reader import pdf_extract

__all__ = [
    "consolidate_memory",
    "retrieve_memory",
    "web_search",
    "html_scraper",
    "pdf_extract"
]

