"""Tool Registry for matching Python functions with JSON schema."""

import inspect
from collections.abc import Callable

from sunday.utils.logging import log


class ToolRegistry:
    """Manages available tools natively passing structured definitions to litellm."""

    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._callbacks: dict[str, Callable] = {}

    def register(self, name: str, description: str, parameters: dict, func: Callable):
        """Register a new python function as a functional tool wrapper."""
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._callbacks[name] = func
        log.debug("tool.registered", name=name)

    def get_tool_schemas(self) -> list[dict]:
        """Fetch array representation schemas for LLM routing requests."""
        return list(self._tools.values())

    async def execute(self, name: str, arguments: dict) -> str:
        """Call a mapped tool natively passing internal arguments securely."""
        if name not in self._callbacks:
            log.warning("tool.execute.missing", name=name)
            return f"Error: Tool '{name}' not found."

        try:
            func = self._callbacks[name]
            log.info("tool.executing", name=name, args=arguments)

            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)

            return str(result)
        except Exception as e:
            log.error("tool.execute.failed", tool=name, error=str(e))
            return f"Error executing constraint '{name}': {str(e)}"
