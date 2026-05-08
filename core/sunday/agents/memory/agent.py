"""Memory Agent utilizing vector semantic recall to construct RAG workflows natively."""

from collections.abc import AsyncGenerator

from sunday.agents.base import AgentCapability, AgentInfo, BaseAgent
from sunday.core.llm.router import LLMRouter
from sunday.database.vector import vector_db
from sunday.models.messages import Message


class MemoryAgent(BaseAgent):
    """Answers queries by strictly analyzing extracted historical memories."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="memory_recall",
            name="Memory Agent",
            description="Recalls information from past conversations using semantic memory search.",
            capabilities=[
                AgentCapability(
                    name="recall",
                    description="Search long-term memory for past information.",
                    keywords=[
                        "remember",
                        "recall",
                        "past",
                        "history",
                        "previously",
                        "earlier",
                        "last time",
                        "mentioned",
                        "i told you",
                        "do you know",
                        "you know",
                        "what did i",
                        "what's my",
                        "what is my",
                        "my favorite",
                        "my name",
                        "who am i",
                        "did i say",
                        "did i mention",
                        "we talked",
                        "we discussed",
                        "you said",
                        "i said",
                        "forget",
                        "have you forgotten",
                    ],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's memory librarian. You have access to past conversation fragments "
            "retrieved from the Vector database via Retrieval-Augmented Generation (RAG). "
            "Answer the user's question directly and accurately using strictly the provided context snippets. "
            "If the retrieved snippets don't contain the answer, inform the user honestly without inventing facts."
            "Always be as concise as possible unless otherwise instructed."
        )

    async def process(self, message: Message, context: list[dict[str, str]]) -> str:
        # Search chromadb
        memories = vector_db.query_memories(message.content, limit=5)

        if memories:
            memory_block = "\n---\n".join([str(m) for m in memories])
            injected_context = [
                {"role": "system", "content": f"Historical Context Retrieved:\n{memory_block}"}
            ]
        else:
            injected_context = [{"role": "system", "content": "No historical context found."}]

        messages = self._build_messages(message, injected_context + context)
        response = await self.llm.generate(messages=messages)
        return response.content

    async def stream(
        self, message: Message, context: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        # Search chromadb
        memories = vector_db.query_memories(message.content, limit=5)

        if memories:
            memory_block = "\n---\n".join([str(m) for m in memories])
            injected_context = [
                {"role": "system", "content": f"Historical Context Retrieved:\n{memory_block}"}
            ]
        else:
            injected_context = [{"role": "system", "content": "No historical context found."}]

        messages = self._build_messages(message, injected_context + context)
        async for token in self.llm.stream(messages=messages):
            yield token
