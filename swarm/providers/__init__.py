"""Provider registry + environment-driven factory.

    from swarm.providers import get_provider
    llm = get_provider()              # picks from $SWARM_PROVIDER, default "mock"
    llm = get_provider("anthropic")   # explicit
"""
from __future__ import annotations

import os

from .base import Completion, LLMProvider, Message
from .mock import MockProvider

_BUILTIN = {"mock": MockProvider}


def get_provider(name: str | None = None, **kwargs) -> LLMProvider:
    name = (name or os.environ.get("SWARM_PROVIDER", "mock")).lower()
    if name in _BUILTIN:
        return _BUILTIN[name](**kwargs)
    # Remote providers imported lazily so core stays dependency-free.
    from .remote import AnthropicProvider, OllamaProvider, OpenAIProvider

    remote = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }
    if name not in remote:
        raise ValueError(f"Unknown provider '{name}'. Known: {sorted({*_BUILTIN, *remote})}")
    return remote[name](**kwargs)


__all__ = ["Completion", "LLMProvider", "Message", "MockProvider", "get_provider"]
