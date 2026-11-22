"""Search swarm: agents that gather and synthesize information.

The search tool is pluggable — wire in a real web/API search by passing a
callable. The default is an offline stub so the capability runs anywhere.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from ...core.agent import Agent
from ...core.blackboard import Blackboard
from ...core.mission import Mission
from ...providers.base import LLMProvider

SearchFn = Callable[[str], Awaitable[list[str]]]


async def _stub_search(query: str) -> list[str]:
    return [f"(stub) result for '{query}' — plug in a real search backend"]


class SearchAgent(Agent):
    role = "information retrieval specialist"
    output_kind = "finding"

    def __init__(self, name: str, provider: LLMProvider, *, search_fn: SearchFn | None = None, angle: str = "") -> None:
        super().__init__(name, provider)
        self.search_fn = search_fn or _stub_search
        self.angle = angle  # lets each agent cover a different sub-query

    async def gather(self, mission: Mission, blackboard: Blackboard) -> dict:
        query = f"{mission.objective} {self.angle}".strip()
        hits = await self.search_fn(query)
        return {"query": query, "hits": " | ".join(hits)}


def build_search_swarm(provider_factory, *, search_fn: SearchFn | None = None, angles: list[str] | None = None):
    angles = angles or ["overview", "recent developments", "risks and caveats"]
    return [
        SearchAgent(f"search-{i}", provider_factory(), search_fn=search_fn, angle=a)
        for i, a in enumerate(angles)
    ]
