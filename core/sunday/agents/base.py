"""Base agent interface — all SUNDAY agents extend this.

This is the contract that every agent must fulfill.
The Orchestrator (Secretary Agent) uses this interface to
route requests and manage agent lifecycle.

DESIGN PRINCIPLES:
1. Every agent is independent — it can function without other agents
2. Every agent declares its capabilities — the router uses this to match tasks
3. Every agent has a system prompt — this defines its personality and expertise
4. Agents communicate through the orchestrator, never directly
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

from sunday.core.llm.router import LLMRouter
from sunday.models.messages import Message


@dataclass
class AgentCapability:
    """Describes something an agent can do."""

    name: str  # e.g., "code_generation", "web_search"
    description: str  # Human-readable description
    keywords: list[str] = field(default_factory=list)  # Matching keywords


@dataclass
class AgentInfo:
    """Metadata about an agent for registration and routing."""

    id: str  # Unique identifier, e.g., "coding", "research"
    name: str  # Display name, e.g., "Coding Agent"
    description: str  # What this agent does
    capabilities: list[AgentCapability] = field(default_factory=list)
    version: str = "0.1.0"
    enabled: bool = True


class BaseAgent(ABC):
    """Abstract base class for all SUNDAY agents."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    @property
    @abstractmethod
    def info(self) -> AgentInfo:
        """Return agent metadata. Used for registration and routing."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt that defines this agent's behavior."""
        ...

    @abstractmethod
    async def process(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> str:
        """Process a message and return a complete response."""
        ...

    @abstractmethod
    async def stream(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Process a message and stream response tokens."""
        ...

    def _build_messages(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Build the full message list for LLM, including system prompt and context."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": message.content})
        return messages
