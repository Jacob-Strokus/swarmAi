"""Real LLM backends: Anthropic, OpenAI, and Ollama.

All three share the same `LLMProvider` contract. `httpx` is imported lazily so
the core swarm (and the mock-driven tests) never require it to be installed.
Keys come from the environment:  ANTHROPIC_API_KEY / OPENAI_API_KEY.
Ollama defaults to a local daemon at http://localhost:11434.
"""
from __future__ import annotations

import os
from typing import Any

from .base import Completion, LLMProvider, Message


def _httpx():
    try:
        import httpx  # noqa: WPS433 (lazy import by design)
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Remote providers need httpx: pip install 'swamai[remote]'"
        ) from exc
    return httpx


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-5-5", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    async def complete(self, messages: list[Message], *, temperature=0.2, max_tokens=1024, **kw) -> Completion:
        httpx = _httpx()
        system = "\n".join(m.content for m in messages if m.role == "system")
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": turns,
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
        text = "".join(block.get("text", "") for block in data.get("content", []))
        return Completion(content=text, raw=data, usage=data.get("usage", {}))


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str = "gpt-4.1", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    async def complete(self, messages: list[Message], *, temperature=0.2, max_tokens=1024, **kw) -> Completion:
        httpx = _httpx()
        turns = [{"role": m.role, "content": m.content} for m in messages]
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": turns,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            r.raise_for_status()
            data = r.json()
        text = data["choices"][0]["message"]["content"]
        return Completion(content=text, raw=data, usage=data.get("usage", {}))


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, model: str = "llama3.1", host: str | None = None) -> None:
        self.model = model
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    async def complete(self, messages: list[Message], *, temperature=0.2, max_tokens=1024, **kw) -> Completion:
        httpx = _httpx()
        turns = [{"role": m.role, "content": m.content} for m in messages]
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": turns,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            r.raise_for_status()
            data = r.json()
        return Completion(content=data["message"]["content"], raw=data)
