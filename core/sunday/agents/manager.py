"""Agent Manager - Auto-discovers and routes between dynamically injected agents."""

import importlib
import inspect
import pkgutil

import sunday.agents
from sunday.agents.base import BaseAgent
from sunday.core.llm.router import LLMRouter
from sunday.utils.logging import log


class AgentManager:
    """Dynamically binds and evaluates Agent implementations inside the /agents directory."""

    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.agents: dict[str, BaseAgent] = {}
        self.default_agent: BaseAgent | None = None
        self._discover_agents()

    def _discover_agents(self) -> None:
        """Scan the python namespace structurally injecting instantiated class bounds natively."""
        package = sunday.agents
        prefix = package.__name__ + "."

        for _, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
            if not modname.endswith(".agent"):
                continue

            try:
                module = importlib.import_module(modname)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseAgent) 
                        and obj.__module__ == module.__name__ 
                        and not inspect.isabstract(obj)
                        and obj.__name__ not in ("BaseAgent", "BaseToolAgent")
                    ):
                        try:
                            agent_instance = obj(llm_router=self.llm_router)
                            agent_id = agent_instance.info.id
                            
                            self.agents[agent_id] = agent_instance
                            log.info("agent_manager.discovered", agent_id=agent_id, class_name=obj.__name__)

                            if agent_id == "secretary":
                                self.default_agent = agent_instance
                        except Exception as e:
                            log.warning("agent_manager.init_failed", class_name=obj.__name__, error=str(e))
                            
            except Exception as e:
                log.warning("agent_manager.import_failed", module=modname, error=str(e))

        if not self.default_agent:
            log.warning("agent_manager.no_default_secretary")

    def determine_agent(self, text: str) -> BaseAgent:
        """Analyze text heuristics over nested agent capability boundaries dynamically."""
        if not self.agents:
            raise RuntimeError("AgentManager contains zero loaded agents.")

        text_lower = text.lower()
        
        for agent in self.agents.values():
            if agent.info.id == "secretary" or not agent.info.enabled:
                continue

            for cap in agent.info.capabilities:
                if any(kw in text_lower for kw in cap.keywords):
                    log.debug("agent_manager.route_matched", agent=agent.info.id, trigger=text[:20])
                    return agent
        
        return self.default_agent if self.default_agent else list(self.agents.values())[0]
