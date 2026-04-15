"""Memory Agent utilizing vector semantic recall to construct RAG workflows natively."""

from collections.abc import AsyncGenerator

from sunday.agents.base import AgentCapability, AgentInfo, BaseAgent
from sunday.database.vector import vector_db
from sunday.core.llm.router import LLMRouter
from sunday.models.messages import Message


class MemoryAgent(BaseAgent):
    """Answers queries by strictly analyzing extracted historical memories."""
    
    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="memory_recall",
            name="Memory Librarian",
            description="Agent that accesses long-term semantic context to remember historical things.",
            capabilities=[
                AgentCapability(
                    name="recall",
                    description="Ability to search long-term memory",
                    keywords=["remember", "recall", "past", "history", "previously"],
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
            injected_context = [{"role": "system", "content": f"Historical Context Retrieved:\n{memory_block}"}]
        else:
            injected_context = [{"role": "system", "content": "No historical context found."}]
            
        messages = self._build_messages(message, injected_context + context)
        response = await self.llm.generate(messages=messages)
        return response.content

    async def stream(self, message: Message, context: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        # Search chromadb
        memories = vector_db.query_memories(message.content, limit=5)
        
        if memories:
            memory_block = "\n---\n".join([str(m) for m in memories])
            injected_context = [{"role": "system", "content": f"Historical Context Retrieved:\n{memory_block}"}]
        else:
            injected_context = [{"role": "system", "content": "No historical context found."}]
            
        messages = self._build_messages(message, injected_context + context)
        async for token in self.llm.stream(messages=messages):
            yield token
