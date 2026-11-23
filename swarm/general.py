"""General-purpose swarm: tell it what to do in plain language.

Instead of hard-coded capability packs (search / ids / recon), a *planner*
reads your free-form objective and spins up a small team of worker roles on the
fly. The workers collaborate over the usual blackboard; a coordinator
synthesizes the result.

    from swarm.general import GeneralSwarm
    from swarm.providers import get_provider

    swarm = GeneralSwarm(lambda: get_provider())
    result = await swarm.run("summarize the tradeoffs of ML-KEM vs classic ECDH")

The planner asks the model to decompose the task into 2–4 specialist roles. If
the model returns nothing parseable (e.g. the offline mock provider), it falls
back to a solver + a critic — enough tension to make the blackboard useful.
"""
from __future__ import annotations

import re
from typing import Callable

from .core.agent import Agent
from .core.mission import Mission
from .core.swarm import Swarm
from .providers.base import LLMProvider, Message

ProviderFactory = Callable[[], LLMProvider]

_PLANNER_SYSTEM = (
    "You are the planner for a swarm of cooperating AI agents. "
    "Given an objective, design a small team (2-4 roles) that should collaborate "
    "to accomplish it. Reply with ONE role per line in the form:\n"
    "name: what this role focuses on\n"
    "No preamble, no numbering, no blank lines."
)

# Default team when planning yields nothing usable. A solver plus a critic is a
# minimal self-checking pair.
_FALLBACK_TEAM = [
    ("solver", "propose a concrete, well-reasoned answer or plan for the objective"),
    ("critic", "red-team the solver's output: find gaps, errors, and missing cases"),
]

_LINE = re.compile(r"^\s*[-*\d.)\s]*([A-Za-z][\w\- ]{0,40}?)\s*[:\-–]\s*(.+?)\s*$")


class GeneralAgent(Agent):
    """A worker whose behavior is defined entirely by its assigned role."""

    output_kind = "finding"


def parse_plan(text: str, *, max_roles: int = 4) -> list[tuple[str, str]]:
    roles: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        m = _LINE.match(raw)
        if not m:
            continue
        name = m.group(1).strip().lower().replace(" ", "-")
        desc = m.group(2).strip()
        if name and name not in seen and len(desc) > 3:
            seen.add(name)
            roles.append((name, desc))
        if len(roles) >= max_roles:
            break
    return roles


class GeneralSwarm:
    def __init__(self, provider_factory: ProviderFactory, *, rounds: int = 2) -> None:
        self.provider_factory = provider_factory
        self.rounds = rounds
        self.last_plan: list[tuple[str, str]] = []

    async def plan(self, objective: str) -> list[tuple[str, str]]:
        provider = self.provider_factory()
        completion = await provider.complete(
            [Message("system", _PLANNER_SYSTEM), Message("user", f"Objective: {objective}")]
        )
        roles = parse_plan(completion.content)
        return roles or list(_FALLBACK_TEAM)

    async def run(self, objective: str, *, max_rounds: int | None = None) -> dict:
        self.last_plan = await self.plan(objective)
        agents = [
            GeneralAgent(name, self.provider_factory(), role=role)
            for name, role in self.last_plan
        ]
        swarm = Swarm(agents, coordinator=self.provider_factory())
        result = await swarm.run(
            Mission(objective=objective, max_rounds=max_rounds or self.rounds)
        )
        result["plan"] = self.last_plan
        return result
