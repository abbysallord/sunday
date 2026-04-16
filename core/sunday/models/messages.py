"""Data models for messages and conversations."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Message author role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageSource(str, Enum):
    """How the message was created."""

    TEXT = "text"
    VOICE = "voice"


class Message(BaseModel):
    """A single message in a conversation."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    role: Role
    content: str
    source: MessageSource = MessageSource.TEXT
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Agent routing info (for future use)
    agent: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class Conversation(BaseModel):
    """A conversation thread."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = "New Conversation"
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str = "sunday-user"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Add a message and update timestamp."""
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

    def get_context_messages(self, max_messages: int = 50) -> list[dict[str, str]]:
        """Get messages formatted for LLM context window."""
        recent = self.messages[-max_messages:]
        return [{"role": msg.role.value, "content": msg.content} for msg in recent]


class ConversationSummary(BaseModel):
    """Lightweight conversation info for sidebar listing."""

    id: str
    title: str
    updated_at: datetime
    message_count: int
    preview: str = ""  # First few words of last message
