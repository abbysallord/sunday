"""The Core Research Agent — handling all real-time internet context mapping."""

import json
from collections.abc import AsyncGenerator

from sunday.agents.base import AgentCapability, AgentInfo, BaseAgent
from sunday.agents.tools.registry import ToolRegistry
from sunday.agents.research.tools import register_research_tools
from sunday.core.llm.router import LLMRouter
from sunday.models.messages import Message
from sunday.utils.logging import log


class ResearchAgent(BaseAgent):
    """An agent that routes deep internet extraction paths over nested LLM tool constraints."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)
        self.registry = ToolRegistry()
        
        # Pull from specific DDG tools 
        register_research_tools(self.registry)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="research_agent",
            name="World Wide Indexer",
            description="Agent that uses live web API connections to verify headlines or documentation context offline.",
            capabilities=[
                AgentCapability(
                    name="web-browsing",
                    description="Ability to parse internet parameters actively.",
                    keywords=["search", "who is", "fetch", "news", "google", "website"],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's dedicated Research Agent. You possess the capability to search "
            "the live internet globally for current news, facts, and deep technical context using DuckDuckGo APIs. "
            "When the user requests verifiable live info, aggressively execute 'search_web'. "
            "If the snippet isn't enough, actively utilize 'fetch_webpage' on specific URLs to cite deep logic natively. "
            "Conclude your execution only when thorough facts have been correctly synthesized."
        )

    async def process(self, message: Message, context: list[dict[str, str]]) -> str:
        """Route tool schema context executing research parameters incrementally."""
        messages = self._build_messages(message, context)
        schemas = self.registry.get_tool_schemas()
        
        for _ in range(5):  # Max 5 chained research searches per request boundary
            response = await self.llm.generate(messages=messages, tools=schemas)
            
            assistant_msg = {"role": "assistant", "content": response.content}
            if response.tool_calls:
                assistant_msg["tool_calls"] = response.tool_calls
            messages.append(assistant_msg)
            
            if not response.tool_calls:
                return response.content or "No findings located."

            for tc in response.tool_calls:
                func_name = tc.get("function", {}).get("name", "")
                try:
                    args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                
                result_str = await self.registry.execute(func_name, args)
                
                messages.append({
                    "role": "tool",
                    "name": func_name,
                    "content": result_str,
                    "tool_call_id": tc.get("id", ""),
                })
        
        return "Search boundaries threshold reached before final correlation."

    async def stream(self, message: Message, context: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        """Wrap synchronous research hooks into synthetic API bounds."""
        final_text = await self.process(message, context)
        
        # Fake structural token yielding because research operates completely asynchronously offline
        chunk_size = 8
        for i in range(0, len(final_text), chunk_size):
            yield final_text[i:i + chunk_size]
