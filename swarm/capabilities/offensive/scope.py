"""Authorization scope — enforced in code, not in a README.

Every active capability must pass each target through a ScopeGuard built from the
mission's explicit authorization list. Out-of-scope targets raise. There is no
"skip the check" flag. This is the control that keeps the offensive capabilities
usable only for authorized security testing (your own assets, or engagements with
written permission).

Scope entries support exact hosts, wildcard subdomains (`*.example.com`), and
CIDR ranges (`10.0.0.0/24`).
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


class ScopeError(PermissionError):
    """Raised when a target is not covered by the mission's authorization scope."""


class ScopeGuard:
    def __init__(self, scope: list[str]) -> None:
        self.hosts: set[str] = set()
        self.wildcards: list[str] = []
        self.networks: list[ipaddress._BaseNetwork] = []
        for raw in scope:
            entry = raw.strip().lower()
            if not entry:
                continue
            if entry.startswith("*."):
                self.wildcards.append(entry[2:])
            elif "/" in entry and _looks_like_cidr(entry):
                self.networks.append(ipaddress.ip_network(entry, strict=False))
            else:
                self.hosts.add(entry)

    @property
    def is_empty(self) -> bool:
        return not (self.hosts or self.wildcards or self.networks)

    def _host_of(self, target: str) -> str:
        if "://" in target:
            return (urlparse(target).hostname or "").lower()
        return target.split("/")[0].split(":")[0].lower()

    def allows(self, target: str) -> bool:
        host = self._host_of(target)
        if not host:
            return False
        if host in self.hosts:
            return True
        for base in self.wildcards:
            if host == base or host.endswith("." + base):
                return True
        if self.networks:
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                ip = None
            if ip is not None and any(ip in net for net in self.networks):
                return True
        return False

    def check(self, target: str) -> str:
        if self.is_empty:
            raise ScopeError(
                "No authorization scope set. Active/offensive actions require an "
                "explicit mission.scope listing targets you are authorized to test."
            )
        if not self.allows(target):
            raise ScopeError(f"Target '{target}' is outside the authorized scope.")
        return target


def _looks_like_cidr(entry: str) -> bool:
    try:
        ipaddress.ip_network(entry, strict=False)
        return True
    except ValueError:
        return False
