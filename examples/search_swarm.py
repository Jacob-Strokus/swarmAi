"""Minimal end-to-end example. Runs fully offline with the mock provider.

    python examples/search_swarm.py
    SWARM_PROVIDER=anthropic ANTHROPIC_API_KEY=... python examples/search_swarm.py
"""
import asyncio

from swarm.capabilities.search import build_search_swarm
from swarm.core import Mission, Swarm
from swarm.providers import get_provider


async def main():
    factory = lambda: get_provider()  # noqa: E731
    agents = build_search_swarm(factory, angles=["overview", "key players", "open problems"])
    swarm = Swarm(agents, coordinator=get_provider())
    result = await swarm.run(Mission(objective="lattice-based post-quantum cryptography", max_rounds=2))
    print(result["report"])


if __name__ == "__main__":
    asyncio.run(main())
