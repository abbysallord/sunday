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
                         "file", "directory", "script", "read file", "write file", "coding",
                        "bash", "shell", "program", "compile", "pwd", "ls",
                        "folder", "refactor"
                    ],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's elite Senior Coding Agent. "
            "You natively possess physical sandbox permissions explicitly mapped to the entire host file system! "
            "WARNING: Do not destructively overwrite core system files recklessly. "
            "To evaluate logic: Use 'list_directory' to find structural endpoints. Use 'read_file' to learn context. "
            "Use 'write_file' to produce complete replacement components natively. Use 'run_shell' to explicitly evaluate your scripts! "
            "Verify all files operate successfully via the terminal loop using python execution bounds before reporting final success."
        )
