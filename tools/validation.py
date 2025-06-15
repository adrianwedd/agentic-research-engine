from __future__ import annotations

"""Utilities for validating user-provided file paths and URLs."""

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

ALLOWED_SCHEMES = {"http", "https", "file"}


class InputValidationError(ValueError):
    """Raised when a path or URL fails validation."""

    status_code = 400


def validate_path_or_url(target: str, allowed_schemes: set[str] | None = None) -> str:
    """Return a sanitized path or URL if ``target`` is valid.

    Parameters
    ----------
    target: str
        User provided file path or URL.
    allowed_schemes: set[str] | None
        Permitted URL schemes. Defaults to ``ALLOWED_SCHEMES``.

    Returns
    -------
    str
        The original URL or a normalized filesystem path.

    Raises
    ------
    InputValidationError
        If the scheme is not allowed or path normalization indicates directory traversal.
    """
    allowed_schemes = allowed_schemes or ALLOWED_SCHEMES
    parsed = urlparse(target)
    scheme = parsed.scheme.lower()
    if scheme and scheme not in allowed_schemes:
        raise InputValidationError(f"Invalid URL scheme: {scheme} (HTTP 400)")

    if scheme in {"http", "https"}:
        return target

    path = unquote(parsed.path) if scheme == "file" else target
    normalized = os.path.normpath(path)
    if ".." in Path(normalized).parts:
        raise InputValidationError(
            "Invalid path: directory traversal detected (HTTP 400)"
        )
    return normalized
