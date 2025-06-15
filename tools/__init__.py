"""Tool package exposing callable wrappers for external services."""

from . import web_search
from .fact_check import fact_check_claim
from .html_scraper import html_scraper
from .ltm_client import consolidate_memory, retrieve_memory
from .pdf_reader import pdf_extract
from .summarizer import summarize_text

__all__ = [
    "consolidate_memory",
    "retrieve_memory",
    "web_search",
    "html_scraper",
    "pdf_extract",
    "summarize_text",
    "fact_check_claim",
]
