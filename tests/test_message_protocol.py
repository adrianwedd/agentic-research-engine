import logging

import pytest
from pydantic import ValidationError

from engine.collaboration.message_protocol import ChatMessage

pytestmark = pytest.mark.core


def test_valid_message():
    msg = ChatMessage.validate_message({"sender": "A", "content": "hi"})
    assert msg.sender == "A"
    assert msg.content == "hi"


def test_invalid_type_logs_error(caplog):
    caplog.set_level(logging.ERROR)
    with pytest.raises(ValidationError):
        ChatMessage.validate_message(
            {"sender": "A", "content": "hi", "message_type": "bad"}
        )
    assert any("Schema violation" in r.message for r in caplog.records)


def test_private_language_warning(caplog):
    caplog.set_level(logging.WARNING)
    ChatMessage.validate_message(
        {"sender": "A", "content": "dGhpcyBpcyBiYXNlNjQgdGV4dA=="}
    )
    assert any("private language" in r.message.lower() for r in caplog.records)
