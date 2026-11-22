"""Shared blackboard: the swarm's collective memory.

Agents don't message each other directly. They post findings here and read what
others posted. This decouples agents, makes runs auditable, and lets you add or
remove roles without rewiring anything.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Entry:
    author: str
    kind: str  # e.g. "finding", "alert", "recon", "summary"
    content: str
    round: int = 0
    tags: tuple[str, ...] = ()
    ts: float = field(default_factory=time.time)


class Blackboard:
    def __init__(self) -> None:
        self._entries: list[Entry] = []
        self._lock = asyncio.Lock()

    async def post(self, entry: Entry) -> None:
        async with self._lock:
            self._entries.append(entry)

    async def read(
        self,
        *,
        kind: str | None = None,
        author: str | None = None,
        exclude_author: str | None = None,
        since_round: int | None = None,
    ) -> list[Entry]:
        async with self._lock:
            rows: Iterable[Entry] = list(self._entries)
        if kind is not None:
            rows = [e for e in rows if e.kind == kind]
        if author is not None:
            rows = [e for e in rows if e.author == author]
        if exclude_author is not None:
            rows = [e for e in rows if e.author != exclude_author]
        if since_round is not None:
            rows = [e for e in rows if e.round >= since_round]
        return list(rows)

    def snapshot(self) -> list[Entry]:
        return list(self._entries)

    def render(self, limit: int = 20) -> str:
        rows = self._entries[-limit:]
        return "\n".join(f"- [{e.author}/{e.kind}] {e.content}" for e in rows) or "(empty)"
