"""Verification Agent — fact-checks claims using live web search."""

from sunday.agents.base import AgentCapability, AgentInfo, BaseToolAgent
from sunday.agents.research.tools import register_research_tools
from sunday.core.llm.router import LLMRouter


class VerificationAgent(BaseToolAgent):
    """Fact-checks claims and returns a structured verdict with evidence."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)
        self._max_loops = 3

    def _register_tools(self) -> None:
        register_research_tools(self.registry)

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="verification",
            name="Verification Agent",
            description="Fact-checks claims using live web search and returns a structured verdict.",
            capabilities=[
                AgentCapability(
                    name="fact_checking",
                    description="Verify claims, check facts, confirm information.",
                    keywords=[
                        "verify",
                        "fact-check",
                        "fact check",
                        "is it true",
                        "is that true",
                        "confirm",
                        "are you sure",
                        "double check",
                        "double-check",
                        "check if",
                        "true or false",
                    ],
                ),
            ],
            version="0.1.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are SUNDAY's Verification Agent. Your sole purpose is to fact-check claims "
            "using live web search. You are skeptical by default.\n\n"
            "PROCESS:\n"
            "1. Search the web for evidence about the claim.\n"
            "2. Evaluate the evidence critically.\n"
            "3. Return a verdict in this exact format:\n\n"
            "**[VERIFIED]** / **[UNVERIFIED]** / **[CONTRADICTED]**\n\n"
            "Then provide: a one-sentence summary, the key evidence, and source URLs.\n\n"
            "RULES:\n"
            "- Never state something is verified without finding corroborating sources.\n"
            "- Distinguish between facts and inferences.\n"
            "- If evidence is mixed, say UNVERIFIED and explain the conflict.\n"
            "- Always cite at least one URL."
        )
