"""The orchestrator.

Runs all agents concurrently for N rounds over a shared blackboard, then lets an
optional coordinator synthesize a final report. Agents see each other's work
between rounds, so later rounds build on earlier findings.
"""
from __future__ import annotations

import asyncio

from ..providers.base import LLMProvider, Message
from .agent import Agent
from .blackboard import Blackboard, Entry
from .mission import Mission


class Swarm:
    def __init__(self, agents: list[Agent], *, coordinator: LLMProvider | None = None) -> None:
        if not agents:
            raise ValueError("A swarm needs at least one agent.")
        self.agents = agents
        self.coordinator = coordinator
        self.blackboard = Blackboard()

    async def run(self, mission: Mission) -> dict:
        for rnd in range(1, mission.max_rounds + 1):
            await asyncio.gather(
                *(a.run_round(mission, self.blackboard, rnd) for a in self.agents)
            )
        report = await self._synthesize(mission)
        return {
            "objective": mission.objective,
            "report": report,
            "entries": [e.__dict__ for e in self.blackboard.snapshot()],
        }

    async def _synthesize(self, mission: Mission) -> str:
        findings = self.blackboard.render(limit=100)
        if self.coordinator is None:
            return f"Mission: {mission.objective}\n\nCollected findings:\n{findings}"
        completion = await self.coordinator.complete(
            [
                Message(
                    "system",
                    "You are the swarm coordinator. Synthesize the agents' findings "
                    "into a single, decision-ready brief. Note agreements, conflicts, "
                    "and the top recommended actions.",
                ),
                Message("user", f"Objective: {mission.objective}\n\nFindings:\n{findings}"),
            ]
        )
        await self.blackboard.post(
            Entry(author="coordinator", kind="summary", content=completion.content, round=mission.max_rounds)
        )
        return completion.content
