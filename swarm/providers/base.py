"""Provider-agnostic LLM interface.

Every backend (Anthropic, OpenAI, Ollama, a mock) implements `LLMProvider`
so the swarm never depends on a specific vendor. Agents talk to this
interface only.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class Completion:
    content: str
    raw: Any = None
    usage: dict[str, int] = field(default_factory=dict)


class LLMProvider(abc.ABC):
    """Minimal async contract shared by all backends."""

    name: str = "base"

    @abc.abstractmethod
    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Completion:
        """Return a single completion for the given message list."""

    async def aclose(self) -> None:  # pragma: no cover - optional cleanup hook
        """Release any held resources (HTTP clients, sockets)."""
        return None
