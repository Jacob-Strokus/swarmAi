"""A Mission is the unit of work handed to a swarm."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mission:
    objective: str
    params: dict[str, Any] = field(default_factory=dict)
    max_rounds: int = 3
    # Authorization scope for any active/offensive capability. Empty = nothing
    # active is allowed. See swarm.capabilities.offensive.scope.ScopeGuard.
    scope: list[str] = field(default_factory=list)
