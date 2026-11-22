"""swamAi — build AI swarms for search, defense, and authorized security testing."""
from .core import Agent, AgentResult, Blackboard, Entry, Mission, Swarm
from .providers import get_provider

__version__ = "0.1.0"
__all__ = ["Agent", "AgentResult", "Blackboard", "Entry", "Mission", "Swarm", "get_provider"]
