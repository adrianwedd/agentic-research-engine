import logging

import pytest

from tools.validation import InputValidationError, validate_path_or_url


def test_log_invalid_path(caplog):
    caplog.set_level(logging.WARNING)
    with pytest.raises(InputValidationError):
        validate_path_or_url("../secret.txt")
    assert any(
        "InputValidationError" in r.message and "../secret.txt" in r.message
        for r in caplog.records
    )
