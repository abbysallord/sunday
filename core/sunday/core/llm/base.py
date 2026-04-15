"""Abstract LLM provider interface.

Every LLM provider (Groq, Google, Ollama, future self-hosted)
implements this interface. The rest of the system never talks
to a provider directly — always through this abstraction.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import StrEnum


class ProviderStatus(StrEnum):
    """Health status of an LLM provider."""

    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class LLMResponse:
    """Structured response from an LLM."""

    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)  # prompt_tokens, completion_tokens
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str  # e.g., "groq", "google", "ollama"

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens one by one."""
        ...

    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Check if this provider is available."""
        ...
