"""Tool package exposing callable wrappers for external services."""

from . import web_search
from .code_interpreter import code_interpreter
from .fact_check import fact_check_claim
from .github_search import github_search
from .html_scraper import html_scraper
from .ltm_client import consolidate_memory, retrieve_memory
from .pdf_reader import pdf_extract
from .summarizer import summarize_text

__all__ = [
    "consolidate_memory",
    "retrieve_memory",
    "web_search",
    "github_search",
    "html_scraper",
    "pdf_extract",
    "summarize_text",
    "fact_check_claim",
    "code_interpreter",
]
