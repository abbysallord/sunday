"""The Core Research Agent — handling all real-time internet context mapping."""

from sunday.agents.base import AgentCapability, AgentInfo, BaseToolAgent
from sunday.agents.research.tools import register_research_tools
from sunday.core.llm.router import LLMRouter


class ResearchAgent(BaseToolAgent):
    """An agent that routes deep internet extraction paths over nested LLM tool constraints."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)
        self._max_loops = 3  # Strictly enforce 3 loops max to bypass API bounds

    def _register_tools(self) -> None:
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
            "the live internet globally for current news, facts, and context using DuckDuckGo. "
            "WARNING: Network API payload limits are extremely sensitive. You must NEVER call 'search_web' "
            "more than 2 times in a single query. Do not loop searches endlessly! Formulate your "
            "best summarization given whatever search data you instantly pull. If looking for recent news or sports scores, ALWAYS evaluate 'timelimit'='w' or 'm' to filter stale data. If no exact data is found, guess or state uncertainty."
        )
