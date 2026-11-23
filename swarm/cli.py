"""swamAi command-line entrypoint.

    python -m swarm search "post-quantum key exchange"
    python -m swarm ids --events sample_events.json
    python -m swarm recon example.com --scope "*.example.com"
"""
from __future__ import annotations

import argparse
import asyncio
import json

from .capabilities.intrusion_detection import build_ids_swarm
from .capabilities.offensive import build_recon_swarm
from .capabilities.search import build_search_swarm
from .core import Mission, Swarm
from .general import GeneralSwarm
from .providers import get_provider


def _factory(name: str | None):
    return lambda: get_provider(name)


async def _chat(args) -> None:
    """General swarm: free-form objective in, synthesized answer out."""
    swarm = GeneralSwarm(_factory(args.provider), rounds=args.rounds)

    async def handle(objective: str) -> None:
        result = await swarm.run(objective)
        team = ", ".join(name for name, _ in result["plan"])
        print(f"\n[swarm assembled: {team}]\n")
        print(result["report"])

    if args.objective:
        await handle(" ".join(args.objective))
        return
    # Interactive REPL.
    print("swamAi — talk to the swarm. Type an objective, or 'exit'.")
    while True:
        try:
            line = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line.lower() in {"exit", "quit", ":q"}:
            break
        if line:
            await handle(line)


async def _run(args) -> None:
    if args.command == "chat":
        await _chat(args)
        return

    provider_name = args.provider
    factory = _factory(provider_name)

    if args.command == "search":
        agents = build_search_swarm(factory)
        mission = Mission(objective=args.query, max_rounds=args.rounds)
    elif args.command == "ids":
        events = json.load(open(args.events)) if args.events else []
        agents = build_ids_swarm(factory)
        mission = Mission(objective="Triage security events", params={"events": events}, max_rounds=args.rounds)
    elif args.command == "recon":
        agents = build_recon_swarm(factory)
        mission = Mission(
            objective=f"Recon of {', '.join(args.targets)}",
            params={"targets": args.targets},
            scope=args.scope,
            max_rounds=args.rounds,
        )
    else:  # pragma: no cover
        raise SystemExit("unknown command")

    swarm = Swarm(agents, coordinator=get_provider(provider_name))
    result = await swarm.run(mission)
    print(result["report"])


def main() -> None:
    p = argparse.ArgumentParser(prog="swarm", description="swamAi swarm runner")
    p.add_argument("--provider", default=None, help="mock|anthropic|openai|ollama (default $SWARM_PROVIDER or mock)")
    p.add_argument("--rounds", type=int, default=2)
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("chat", help="talk to a general swarm; omit text for interactive mode")
    c.add_argument("objective", nargs="*", help="free-form objective (quotes optional)")

    s = sub.add_parser("search")
    s.add_argument("query")

    i = sub.add_parser("ids")
    i.add_argument("--events", help="path to JSON list of events")

    r = sub.add_parser("recon")
    r.add_argument("targets", nargs="+")
    r.add_argument("--scope", nargs="*", default=[], help="authorized hosts/CIDRs, e.g. *.example.com 10.0.0.0/24")

    args = p.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
