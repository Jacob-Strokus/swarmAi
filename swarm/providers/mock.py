"""Deterministic offline provider.

Lets the whole swarm run with zero API keys and zero network — used by tests,
demos, and CI. It echoes structured, context-aware text so multi-agent
collaboration is observable without a real model.
"""
from __future__ import annotations

from .base import Completion, LLMProvider, Message


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, persona: str = "analyst") -> None:
        self.persona = persona

    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Completion:
        system = next((m.content for m in messages if m.role == "system"), "")
        user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        role_hint = system.strip().splitlines()[0] if system else self.persona
        # Deterministic, context-referencing output.
        body = (
            f"[{role_hint}] assessment: reviewed {len(user)} chars of context. "
            f"Key signal: {_first_signal(user)}. "
            f"Recommended next action: hand findings to peers via the blackboard."
        )
        return Completion(content=body, usage={"input_tokens": len(user), "output_tokens": len(body)})


def _first_signal(text: str) -> str:
    for line in text.splitlines():
        line = line.strip("-* \t")
        if line:
            return line[:120]
    return "no actionable signal yet"
