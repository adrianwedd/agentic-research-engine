from __future__ import annotations

"""Message schema for group chat communication."""

import logging
import re
import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Allowed categories of chat messages."""

    message = "message"
    question = "question"
    finding = "finding"
    proposal = "proposal"
    command = "command"
    finish = "finish"


_PRIVATE_LANG_RE = re.compile(r"[A-Za-z0-9+/]{20,}=?")


class ChatMessage(BaseModel):
    """Structured message passed between agents in a group chat."""

    sender: str = Field(..., description="ID of the sending agent")
    content: str = Field(..., description="Message text")
    type: MessageType = Field(
        default=MessageType.message,
        alias="message_type",
        description="Category of the message",
    )
    recipient: Optional[str] = Field(
        None, description="Optional ID of the intended recipient"
    )
    timestamp: float = Field(default_factory=time.time, description="Message timestamp")

    model_config = {"populate_by_name": True}

    @field_validator("content")
    @classmethod
    def _check_private_language(cls, value: str) -> str:
        if not value:
            raise ValueError("content must not be empty")
        if _PRIVATE_LANG_RE.search(value):
            logger.warning(
                "Potential private language detected in message: %s", value[:30]
            )
        return value

    @classmethod
    def validate_message(cls, message: dict | "ChatMessage") -> "ChatMessage":
        """Validate and return a ``ChatMessage`` instance."""
        try:
            if isinstance(message, cls):
                obj = message
            else:
                obj = cls.model_validate(message)
        except ValidationError as exc:
            logger.error("Schema violation: %s", exc)
            raise
        return obj
