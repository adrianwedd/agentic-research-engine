from __future__ import annotations

"""Message schema for group chat communication."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Structured message passed between agents in a group chat."""

    sender: str = Field(..., description="ID of the sending agent")
    content: str = Field(..., description="Message text")
    type: str = Field("message", alias="message_type", description="Category of the message")
    recipient: Optional[str] = Field(
        None, description="Optional ID of the intended recipient"
    )

    model_config = {"populate_by_name": True}

