"""Agent base class.

An agent has a *role* (its system prompt), an LLM *provider* (its brains), and
an optional set of *tools* (functions it can call to gather real data). Each
round it runs `step()`: gather data with tools, then reason over the blackboard
with the provider, then post a finding.

Capability agents (search, IDS, recon) subclass this and override `gather()` to
pull their domain-specific data before reasoning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..providers.base import LLMProvider, Message
from .blackboard import Blackboard, Entry
from .mission import Mission


@dataclass
class AgentResult:
    content: str
    kind: str = "finding"
    tags: tuple[str, ...] = ()
    data: dict[str, Any] = field(default_factory=dict)


class Agent:
    #: One-line role description used as the first line of the system prompt.
    role: str = "generic analyst"
    #: What kind of blackboard entry this agent produces.
    output_kind: str = "finding"

    def __init__(self, name: str, provider: LLMProvider, *, role: str | None = None) -> None:
        self.name = name
        self.provider = provider
        if role:
            self.role = role

    def system_prompt(self, mission: Mission) -> str:
        return (
            f"{self.role}\n"
            f"You are '{self.name}', one agent in a cooperating swarm.\n"
            f"Mission objective: {mission.objective}\n"
            "Be concise. Report only new, actionable signal. Defer to peers' findings."
        )

    async def gather(self, mission: Mission, blackboard: Blackboard) -> dict[str, Any]:
        """Collect domain data with tools before reasoning. Override in subclasses."""
        return {}

    async def step(self, mission: Mission, blackboard: Blackboard, *, round: int) -> AgentResult:
        data = await self.gather(mission, blackboard)
        peers = await blackboard.read(exclude_author=self.name)
        peer_text = "\n".join(f"- [{e.author}] {e.content}" for e in peers[-15:]) or "(none yet)"
        data_text = "\n".join(f"{k}: {v}" for k, v in data.items()) or "(no tool data)"
        user = (
            f"Peer findings so far:\n{peer_text}\n\n"
            f"Your tool data this round:\n{data_text}\n\n"
            f"Round {round}. Produce your contribution."
        )
        completion = await self.provider.complete(
            [Message("system", self.system_prompt(mission)), Message("user", user)]
        )
        return AgentResult(content=completion.content, kind=self.output_kind, data=data)

    async def run_round(self, mission: Mission, blackboard: Blackboard, round: int) -> Entry:
        result = await self.step(mission, blackboard, round=round)
        entry = Entry(
            author=self.name,
            kind=result.kind,
            content=result.content,
            round=round,
            tags=result.tags,
        )
        await blackboard.post(entry)
        return entry
