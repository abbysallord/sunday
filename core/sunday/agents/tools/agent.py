"""Tool Calling Agent — executes physical procedures within the local system bounds."""
import json
from collections.abc import AsyncGenerator

from sunday.agents.base import AgentCapability, AgentInfo, BaseAgent
from sunday.agents.tools.registry import ToolRegistry
from sunday.agents.tools.builtins import register_builtins
from sunday.core.llm.router import LLMRouter
from sunday.models.messages import Message
from sunday.utils.logging import log


class ToolCallingAgent(BaseAgent):
    """An agent that supports continuous functional executions dynamically routing API responses."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)
        self.registry = ToolRegistry()
        register_builtins(self.registry)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="tool_runner",
            name="Utility Executor",
            description="Agent specialized in determining logic chains and invoking native machine APIs.",
            capabilities=[
                AgentCapability(
                    name="execution",
                    description="Ability to run native system tools.",
                    keywords=["time", "calculate", "system", "run", "do"],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's primary function execution agent. "
            "You have direct access to system-level tools. "
            "Evaluate the user's request. If it demands real-time data, calculations, "
            "or actions that you cannot answer logically from raw memory, execute the provided tools. "
            "Execute tools cleanly. If multiple tools are needed, use them in sequence."
        )

    async def process(self, message: Message, context: list[dict[str, str]]) -> str:
        """Fully execute a tool loop and return the final textual response."""
        messages = self._build_messages(message, context)
        schemas = self.registry.get_tool_schemas()
        
        for _ in range(5):  # Max 5 chained tool calls per message
            response = await self.llm.generate(messages=messages, tools=schemas)
            
            # Append the LLM's raw response to keep the sequence valid
            # LiteLLM formats this nicely if we include tool_calls directly
            assistant_msg = {
                "role": "assistant",
                "content": response.content,
            }
            if response.tool_calls:
                assistant_msg["tool_calls"] = response.tool_calls
            messages.append(assistant_msg)
            
            if not response.tool_calls:
                # Exiting early since LLM concluded the function calling phase
                return response.content

            # Attempt all triggered tool calls sequentially
            for tc in response.tool_calls:
                func_name = tc.get("function", {}).get("name", "")
                try:
                    args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                
                # Natively call defined python execution
                result_str = await self.registry.execute(func_name, args)
                
                # Pass back result
                messages.append({
                    "role": "tool",
                    "name": func_name,
                    "content": result_str,
                    "tool_call_id": tc.get("id", ""),
                })
        
        return "Executed maximum tool threshold. Stopping execution chain to preserve API limits."

    async def stream(self, message: Message, context: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        """Handles tool resolution, and streams final text block artificially."""
        final_text = await self.process(message, context)
        # Yield the generated text block dynamically to mimic token streaming visually
        chunk_size = 8
        for i in range(0, len(final_text), chunk_size):
            yield final_text[i:i + chunk_size]
