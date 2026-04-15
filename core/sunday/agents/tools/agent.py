"""The System Tooling Agent handling local desktop executions autonomously."""

from sunday.agents.base import AgentCapability, AgentInfo, BaseToolAgent
from sunday.agents.tools.builtins import register_builtins


class ToolCallingAgent(BaseToolAgent):
    """An agent that translates natural language into direct system tool executions natively."""

    def _register_tools(self) -> None:
        register_builtins(self.registry)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="tool_agent",
            name="System Tool Operator",
            description="Agent that controls isolated logical loops structurally natively.",
            capabilities=[
                AgentCapability(
                    name="system_tools",
                    description="Mathematical reasoning, python scripts, or evaluating desktop timeframes.",
                    keywords=[
                        "time",
                        "clock",
                        "calculate",
                        "math",
                        "maths",
                        "+",
                        "-",
                        "*",
                        "/",
                        "operating system",
                        "system info",
                        "os",
                        "platform",
                        "run tool",
                        "python",
                        "script",
                        "code",
                    ],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's primary Tool Calling Agent. You possess the explicit ability "
            "to bridge natural language queries internally into direct physical code executions! "
            "Use your registered tools immediately to evaluate logic arrays. Return the exact response clearly and precisely to the user."
        )
