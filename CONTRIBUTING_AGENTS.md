# Building Advanced Agents in SUNDAY

SUNDAY is designed with a deeply modular, auto-discovering multi-agent architecture. If you want to contribute an entirely new Agent (e.g. `CodingAgent` or `VisionAgent`), you do not need to touch the WebSocket router or learn `litellm` streaming pipelines.

The Orchestrator (`AgentManager`) will automatically find, instantiate, and route websocket messages to your agent simply if you drop it into the `core/sunday/agents/` folder!

## The Workflow

### 1. Create your Folder
Create a folder named identically to your agent concept inside `core/sunday/agents/`.
**CRITICAL**: You must include an `__init__.py` file so the agent auto-discovery engine can read your folder!

```bash
mkdir core/sunday/agents/coding
touch core/sunday/agents/coding/__init__.py
touch core/sunday/agents/coding/agent.py
```

### 2. Define the Logic
If your Agent does not require explicitly looping over standard physical Python tools (e.g., retrieving facts directly from memory endpoints without iterative hooks), inherit from `BaseAgent`.

Otherwise, if your Agent relies dynamically on `tools` (nearly 90% of all future agents like CyberSecurity, Copilot, etc.), inherit strictly from `BaseToolAgent`. The `BaseToolAgent` totally abstracts away all JSON schema parameters, loop constraints, and LLM boundaries!

```python
# core/sunday/agents/coding/agent.py

from sunday.agents.base import AgentCapability, AgentInfo, BaseToolAgent
from sunday.core.llm.router import LLMRouter
from sunday.agents.tools.registry import ToolRegistry

# 1. Define typical helper functions
def execute_terminal_run(command: str) -> str:
    """Helper code executing directly inside bash env structure."""
    return f"Simulated output of {command}"

def register_hooks(registry: ToolRegistry):
    registry.register(
        name="run_bash", 
        description="Run bash execution natively", 
        parameters=...,
        func=execute_terminal_run
    )

class CodingAgent(BaseToolAgent):
    """A Contributor designed Agent extending Python code dynamically."""
    
    def _register_tools(self) -> None:
        # Register the local tools above
        register_hooks(self.registry)

    @property
    def info(self) -> AgentInfo:
        # Define EXPLICIT keywords. This is exactly how the system routes users to your new agent!
        return AgentInfo(
            id="coding_agent",
            name="Senior Developer Interface",
            description="Agent that reads/writes codebase parameters implicitly.",
            capabilities=[
                AgentCapability(
                    name="programming",
                    description="Ability to rewrite code parameters.",
                    keywords=["code", "write a script", "debug", "python", "javascript"],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return "You are SUNDAY's elite code execution agent. Use your tools wisely."

```

### You're Done!
That is literally everything required!
- Do not edit `handler.py`. 
- Do not edit the LLM generation routers.
- The next time the User asks `"Please code a python script"`, the underlying `AgentManager` will catch the `keywords=["code", "python"]` from your info property natively, instantiate your Class, and wire your custom tools together effortlessly.
