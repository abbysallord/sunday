from sunday.agents.manager import AgentManager
from sunday.core.llm.router import LLMRouter

router = LLMRouter()
am = AgentManager(router)
print("Loaded agents:", list(am.agents.keys()))

agent1 = am.determine_agent("search the internet")
print("Agent for 'search the internet':", agent1.info.id)

agent2 = am.determine_agent("what is 5233 prime")
print("Agent for 'what is 5233 prime':", getattr(agent2.info, "id", "None"))
