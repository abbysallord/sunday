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
            "You are SUNDAY's Coding Agent, an elite AI developer. You have full access to the host file system "
            "and can execute shell commands.\n\n"
            "WORKFLOW:\n"
            "1. PLAN: Always start by outputting an `<implementation_plan>` block detailing what files you will read/edit.\n"
            "2. EXPLORE: Use `list_directory` or `grep_search` to find what you need quickly.\n"
            "3. READ: Use `read_file` with `start_line` and `end_line` to read large files in chunks without blowing up your context window.\n"
            "4. SURGICAL EDITS: Use `multi_replace_file_content` to make exact line edits. DO NOT use `write_file` to edit existing files.\n"
            "5. EXECUTE: Use `run_shell` to execute scripts or run tests to verify your changes work.\n\n"
            "RULES:\n"
            "- TOKEN EFFICIENCY: Never load a whole file if you only need one function. Never rewrite a whole file to fix a typo.\n"
            "- Never delete system-critical files.\n"
            "- If a command fails, read the error and fix it."
        )
