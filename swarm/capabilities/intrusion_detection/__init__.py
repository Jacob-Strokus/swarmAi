"""Intrusion-detection swarm (defensive).

Detector agents run cheap, deterministic rules over a stream of events, then the
LLM triages what fired — reducing alert fatigue by explaining and prioritizing.
Detectors are plain functions, easy to unit-test and extend.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Callable

from ...core.agent import Agent
from ...core.blackboard import Blackboard
from ...core.mission import Mission
from ...providers.base import LLMProvider

# A detector takes the event list and returns (signal_name, detail) pairs.
Detector = Callable[[list[dict]], list[tuple[str, str]]]


def failed_login_bursts(events: list[dict], threshold: int = 5) -> list[tuple[str, str]]:
    by_ip = Counter(e.get("src_ip") for e in events if e.get("event") == "auth_fail")
    return [("brute_force_suspected", f"{ip}: {n} failed logins") for ip, n in by_ip.items() if n >= threshold]


def suspicious_user_agents(events: list[dict]) -> list[tuple[str, str]]:
    bad = re.compile(r"sqlmap|nikto|nmap|curl/|python-requests", re.I)
    out = []
    for e in events:
        ua = str(e.get("user_agent", ""))
        if bad.search(ua):
            out.append(("scanner_ua", f"{e.get('src_ip','?')} -> {ua}"))
    return out


def egress_to_rare_ports(events: list[dict], common={80, 443, 53, 22}) -> list[tuple[str, str]]:
    out = []
    for e in events:
        if e.get("event") == "egress" and e.get("dst_port") not in common:
            out.append(("rare_egress", f"{e.get('src_ip','?')} -> :{e.get('dst_port')}"))
    return out


DEFAULT_DETECTORS: list[Detector] = [failed_login_bursts, suspicious_user_agents, egress_to_rare_ports]


class IDSAgent(Agent):
    role = "intrusion-detection analyst (defensive SOC)"
    output_kind = "alert"

    def __init__(self, name: str, provider: LLMProvider, *, detectors: list[Detector] | None = None) -> None:
        super().__init__(name, provider)
        self.detectors = detectors or DEFAULT_DETECTORS

    async def gather(self, mission: Mission, blackboard: Blackboard) -> dict:
        events = mission.params.get("events", [])
        fired: list[tuple[str, str]] = []
        for det in self.detectors:
            fired.extend(det(events))
        return {
            "events_seen": str(len(events)),
            "signals": " ; ".join(f"{name}: {detail}" for name, detail in fired) or "none",
        }


def build_ids_swarm(provider_factory, *, detectors: list[Detector] | None = None, n: int = 1):
    return [IDSAgent(f"ids-{i}", provider_factory(), detectors=detectors) for i in range(n)]
