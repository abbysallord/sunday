"""Agent Manager — auto-discovers agents and routes with confidence scoring."""

import importlib
import inspect
import pkgutil
import re

import sunday.agents
from sunday.agents.base import BaseAgent
from sunday.core.llm.router import LLMRouter
from sunday.utils.logging import log

# Minimum score for a non-default agent to win routing
_ROUTE_THRESHOLD = 1.0


def _score_agent(text_lower: str, keywords: list[str]) -> float:
    """Score how well a text matches a keyword list.

    Rules:
    - Each keyword match = 1.0 point
    - Keyword near start of sentence (first 40 chars) = +0.5 bonus
    - Multi-word keyword match = +0.5 bonus (more specific)
    - Negation prefix ("don't", "can't", "not") within 3 words before keyword = -2.0
    """
    score = 0.0
    negation_pattern = re.compile(
        r"\b(don'?t|can'?t|cannot|not|never|no)\b\s+(?:\w+\s+){0,2}"
    )

    for kw in keywords:
        if kw not in text_lower:
            continue

        idx = text_lower.find(kw)

        # Check for negation in the 30 chars before the keyword
        prefix = text_lower[max(0, idx - 30) : idx]
        if negation_pattern.search(prefix):
            score -= 2.0
            continue

        score += 1.0
        if idx < 40:
            score += 0.5
        if " " in kw:  # multi-word keyword is more specific
            score += 0.5

    return score


class AgentManager:
    """Discovers and routes to agents using confidence scoring."""

    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.agents: dict[str, BaseAgent] = {}
        self.default_agent: BaseAgent | None = None
        self._discover_agents()

    def _discover_agents(self) -> None:
        package = sunday.agents
        prefix = package.__name__ + "."

        for _, modname, _ispkg in pkgutil.walk_packages(package.__path__, prefix):
            if not modname.endswith(".agent"):
                continue
            try:
                module = importlib.import_module(modname)
                for _name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseAgent)
                        and obj.__module__ == module.__name__
                        and not inspect.isabstract(obj)
                        and obj.__name__ not in ("BaseAgent", "BaseToolAgent")
                    ):
                        try:
                            instance = obj(llm_router=self.llm_router)
                            agent_id = instance.info.id
                            self.agents[agent_id] = instance
                            log.info("agent_manager.discovered", agent_id=agent_id)
                            if agent_id == "secretary":
                                self.default_agent = instance
                        except Exception as e:
                            log.warning("agent_manager.init_failed", class_name=obj.__name__, error=str(e))
            except Exception as e:
                log.warning("agent_manager.import_failed", module=modname, error=str(e))

        if not self.default_agent:
            log.warning("agent_manager.no_default_secretary")

    def determine_agent(self, text: str) -> BaseAgent:
        """Route to the highest-scoring agent above threshold, else default."""
        if not self.agents:
            raise RuntimeError("No agents loaded.")

        text_lower = text.lower()
        best_agent: BaseAgent | None = None
        best_score = 0.0

        for agent in self.agents.values():
            if agent.info.id == "secretary" or not agent.info.enabled:
                continue

            agent_score = 0.0
            for cap in agent.info.capabilities:
                agent_score += _score_agent(text_lower, cap.keywords)

            if agent_score > best_score:
                best_score = agent_score
                best_agent = agent

        if best_agent and best_score >= _ROUTE_THRESHOLD:
            log.debug("agent_manager.routed", agent=best_agent.info.id, score=best_score)
            return best_agent

        log.debug("agent_manager.default", score=best_score)
        return self.default_agent if self.default_agent else list(self.agents.values())[0]
