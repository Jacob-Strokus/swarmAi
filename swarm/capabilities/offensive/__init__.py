"""Offensive capability pack — authorized security testing only.

Scope: this pack is for reconnaissance and assessment against assets you own or
are contractually authorized to test. Every network action is gated by
`ScopeGuard` (see scope.py); out-of-scope targets are refused in code.

What lives here: passive/light reconnaissance primitives (DNS resolution, HTTP
service fingerprinting) that every legitimate pentest and attack-surface-
management workflow uses. Weaponized exploitation, malware, and payload delivery
are deliberately out of scope for this framework.
"""
from __future__ import annotations

import asyncio
import socket
from urllib.request import Request, urlopen

from ...core.agent import Agent
from ...core.blackboard import Blackboard
from ...core.mission import Mission
from ...providers.base import LLMProvider
from .scope import ScopeError, ScopeGuard

__all__ = ["ReconAgent", "ScopeGuard", "ScopeError", "build_recon_swarm"]


def _dns_lookup(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except OSError as exc:
        return f"unresolved ({exc.__class__.__name__})"


def _http_fingerprint(target: str, timeout: float = 5.0) -> str:
    url = target if "://" in target else f"http://{target}"
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "swamAi-recon/0.1"})
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (scope-gated)
            server = resp.headers.get("Server", "unknown")
            powered = resp.headers.get("X-Powered-By", "")
            return f"HTTP {resp.status} Server={server} {('X-Powered-By=' + powered) if powered else ''}".strip()
    except Exception as exc:  # noqa: BLE001 - recon is best-effort
        return f"no HTTP banner ({exc.__class__.__name__})"


class ReconAgent(Agent):
    role = "reconnaissance analyst (authorized engagement)"
    output_kind = "recon"

    async def gather(self, mission: Mission, blackboard: Blackboard) -> dict:
        guard = ScopeGuard(mission.scope)
        targets = mission.params.get("targets", [])
        results: dict[str, str] = {}
        for target in targets:
            try:
                guard.check(target)
            except ScopeError as exc:
                results[target] = f"SKIPPED — {exc}"
                continue
            host = guard._host_of(target)
            loop = asyncio.get_event_loop()
            ip = await loop.run_in_executor(None, _dns_lookup, host)
            banner = await loop.run_in_executor(None, _http_fingerprint, target)
            results[target] = f"ip={ip}; {banner}"
        return {"recon": " || ".join(f"{t}: {r}" for t, r in results.items()) or "no targets"}


def build_recon_swarm(provider_factory, n: int = 1):
    return [ReconAgent(f"recon-{i}", provider_factory()) for i in range(n)]
