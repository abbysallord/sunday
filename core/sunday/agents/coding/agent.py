"""The elite Coding Agent capable of reading/writing system codebases physically."""

from sunday.agents.base import AgentCapability, AgentInfo, BaseToolAgent
from sunday.agents.coding.tools import register_coding_tools
from sunday.core.llm.router import LLMRouter


class CodingAgent(BaseToolAgent):
    """An execution-heavy AI Agent capable of modifying existing project scopes cleanly."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)
        self._max_loops = 5  # Allow multi-file tracking sequences securely

    def _register_tools(self) -> None:
        register_coding_tools(self.registry)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="coding_agent",
            name="Senior Developer Interface",
            description="Agent orchestrating explicit OS modifications and codebase evaluation loops natively.",
            capabilities=[
                AgentCapability(
                    name="programming_and_shell",
                    description="Ability to construct python code or bash environments globally seamlessly.",
                    keywords=[
                        "file",
                        "directory",
                        "script",
                        "read file",
                        "write file",
                        "coding",
                        "bash",
                        "shell",
                        "program",
                        "compile",
                        "pwd",
                        "ls",
                        "folder",
                        "refactor",
                    ],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's Coding Agent. You have full access to the host file system "
            "and can execute shell commands.\n\n"
            "WORKFLOW:\n"
            "1. Use 'list_directory' to explore the file structure.\n"
            "2. Use 'read_file' to understand existing code.\n"
            "3. Use 'write_file' to create or modify files.\n"
            "4. Use 'run_shell' to execute commands (e.g., run scripts, install packages).\n\n"
            "RULES:\n"
            "- Always verify your changes work by running them.\n"
            "- Never delete system-critical files.\n"
            "- Explain what you're doing at each step.\n"
            "- If a command fails, read the error and fix it."
        )
