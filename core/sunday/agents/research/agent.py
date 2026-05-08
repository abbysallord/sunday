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
            name="Research Agent",
            description="Searches the live internet for current information, news, and facts.",
            capabilities=[
                AgentCapability(
                    name="web_search",
                    description="Search the internet for real-time information.",
                    keywords=[
                        "search",
                        "look up",
                        "find out",
                        "who is",
                        "latest",
                        "news",
                        "current",
                        "recent",
                        "google",
                        "website",
                        "fetch",
                        "browse",
                        "web",
                        "internet",
                        "find information",
                        "search for",
                        "look up",
                    ],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's Research Agent. You can search the live internet for current "
            "information using DuckDuckGo.\n\n"
            "INSTRUCTIONS:\n"
            "1. ALWAYS use the 'search_web' tool to find information. Do NOT say you can't search.\n"
            "2. For recent events or news, set timelimit='w' (week) or 'm' (month).\n"
            "3. If the first search doesn't find enough, try ONE more search with refined terms.\n"
            "4. After getting search results, summarize the findings clearly with source URLs.\n"
            "5. If search returns no results, say so honestly — don't make up information.\n"
            "6. Use 'fetch_webpage' to read a specific page for more detail when needed.\n"
            "7. Maximum 2 tool calls per query to stay within rate limits."
        )
