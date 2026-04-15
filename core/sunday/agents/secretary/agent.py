"""Secretary Agent — the default conversational agent and future orchestrator.

This is the first agent and handles all direct conversation.
In future phases, this evolves into the orchestrator that routes
requests to specialized agents.
"""

from collections.abc import AsyncGenerator

from sunday.agents.base import AgentCapability, AgentInfo, BaseAgent
from sunday.agents.secretary.prompts import SECRETARY_SYSTEM_PROMPT
from sunday.core.llm.router import LLMRouter
from sunday.models.messages import Message


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

    async def process(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> str:
        messages = self._build_messages(message, context)
        response = await self.llm.generate(messages=messages)
        return response.content

    async def stream(
        self,
        message: Message,
        context: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(message, context)
        async for token in self.llm.stream(messages=messages):
            yield token
