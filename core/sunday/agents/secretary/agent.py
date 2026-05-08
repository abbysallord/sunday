"""Secretary Agent — the default conversational agent and future orchestrator.

This is the first agent and handles all direct conversation.
In future phases, this evolves into the orchestrator that routes
requests to specialized agents.
"""

from collections.abc import AsyncGenerator

from sunday.agents.base import AgentCapability, AgentInfo, BaseAgent
from sunday.agents.secretary.prompts import SECRETARY_SYSTEM_PROMPT
from sunday.core.llm.router import LLMRouter
from sunday.database.vector import vector_db
from sunday.models.messages import Message
from sunday.utils.logging import log


class SecretaryAgent(BaseAgent):
    """Default conversational agent — handles everything until specialized agents exist."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="secretary",
            name="Secretary",
            description="Default conversational agent. Handles general queries and routes to specialists.",
            capabilities=[
                AgentCapability(
                    name="conversation",
                    description="General conversation and Q&A",
                    keywords=["chat", "talk", "question", "help"],
                ),
                AgentCapability(
                    name="reasoning",
                    description="Analysis and logical reasoning",
                    keywords=["analyze", "think", "reason", "explain"],
                ),
                AgentCapability(
                    name="writing",
                    description="Writing, editing, and content creation",
                    keywords=["write", "edit", "draft", "compose"],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return SECRETARY_SYSTEM_PROMPT

    def _inject_memories(
        self, message: Message, context: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Inject top-3 relevant memories from ChromaDB into the context.

        This gives the Secretary passive memory recall even when the
        Memory Agent isn't explicitly routed to.
        """
        try:
            memories = vector_db.query_memories(message.content, limit=3)
            if memories:
                memory_block = "\n---\n".join(memories)
                return [
                    {
                        "role": "system",
                        "content": (
                            "Relevant context from past conversations "
                            "(use if helpful, ignore if not relevant):\n"
                            f"{memory_block}"
                        ),
                    }
                ] + context
        except Exception as e:
            log.warning("secretary.memory_inject_failed", error=str(e))

        return context

    async def process(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> str:
        enriched_context = self._inject_memories(message, context)
        messages = self._build_messages(message, enriched_context)
        response = await self.llm.generate(messages=messages)
        return response.content

    async def stream(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        enriched_context = self._inject_memories(message, context)
        messages = self._build_messages(message, enriched_context)
        async for token in self.llm.stream(messages=messages):
            yield token
