# swarmAI

Build **AI swarms** — small teams of cooperating agents — and just **tell them
what to do**. A planner reads your plain-language objective and assembles a team
on the fly; the agents collaborate over a shared **blackboard**; a coordinator
synthesizes the result. No need to hand-code roles for every task.

- **Talk to it.** `swarm chat "..."` — the planner designs the team per objective.
- **Provider-agnostic brains.** One `LLMProvider` interface; swap Claude, GPT,
  or a local Ollama model with an env var. Runs fully offline with a built-in
  mock provider (no keys, no network).
- **Python core, Rust hot paths.** Orchestration in Python; a Cargo workspace
  (`crates/`) for performance-critical pieces, exposed via PyO3/maturin.
- **Specialist packs when you want them.** Ready-made `search`, `intrusion_detection`,
  and scope-gated `offensive` swarms are still there for fixed workflows.

## Architecture

```
"do X"  ──►  Planner  ──►  assembles 2–4 roles for this objective
                               │        │        │
                               ▼        ▼        ▼
                     ┌──────────── Blackboard ────────────┐   shared state:
                     │   findings · critiques · results   │   every agent reads
                     └─────────────────┬──────────────────┘   peers' work each round
                                       ▼
                                 Coordinator ──► decision-ready answer
```

- **`swarm/general.py`** — `GeneralSwarm` + planner (the default way in).
- **`swarm/core/`** — `Agent`, `Swarm`, `Blackboard`, `Mission`.
- **`swarm/providers/`** — `mock`, `anthropic`, `openai`, `ollama` behind one interface.
- **`swarm/capabilities/`** — fixed-role packs: `search`, `intrusion_detection`, `offensive`.

## Quick start

```bash
pip install -e ".[dev]"      # core + test deps (no keys needed)
pytest                       # all green, fully offline

python -m swarm chat "compare ML-KEM and ECDH for a new protocol"   # one-shot
python -m swarm chat                                                # interactive REPL
```

Point it at a real model with env vars:

```bash
SWARM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-... python -m swarm chat "..."
SWARM_PROVIDER=ollama    python -m swarm chat "..."      # local, offline
```

With the mock provider the planner falls back to a **solver + critic** pair so
everything runs keyless. With a real model it tailors the team to the objective.

## Programmatic use

```python
import asyncio
from swarm.general import GeneralSwarm
from swarm.providers import get_provider

swarm = GeneralSwarm(lambda: get_provider())      # $SWARM_PROVIDER, default mock
result = asyncio.run(swarm.run("summarize the tradeoffs of ML-KEM vs ECDH"))
print(result["plan"])     # the roles the planner assembled
print(result["report"])   # the synthesized answer
```

## Specialist packs

For fixed workflows you don't need to re-plan each time:

| Pack | What it does | Status |
|------|--------------|--------|
| `search` | Agents cover different angles of a query, synthesize into one brief. Pluggable backend. | ✅ |
| `intrusion_detection` | Deterministic detectors (brute-force, scanner UAs, rare egress) + LLM triage. Defensive. | ✅ |
| `offensive` | Scope-gated reconnaissance (DNS, HTTP fingerprint) for authorized testing. | ✅ |

```bash
python -m swarm search "post-quantum key exchange"
python -m swarm ids --events events.json
python -m swarm recon app.example.com --scope "*.example.com"
```

## Responsible use

The `offensive` pack is for **reconnaissance and assessment of assets you own or
are contractually authorized to test**. Authorization is enforced *in code*:
every active action passes through `ScopeGuard`, built from the mission's
explicit `scope`. No scope → nothing active runs. The framework intentionally
**does not** include exploitation payloads, malware, or delivery mechanisms.
See [`SECURITY.md`](SECURITY.md).

## Roadmap

- [x] Provider-agnostic LLM backend (mock / Anthropic / OpenAI / Ollama)
- [x] Blackboard orchestration + fixed capability packs
- [x] General-purpose swarm — plan a team from a plain-language objective
- [ ] **Dev harness** — self-improving loop to build swarmAI: create → test → PR →
      review → merge, looping back with feedback. Human on the merge gate while the
      test suite and review step mature.
- [ ] LLM-driven tool calling (agents invoke tools themselves, across providers)
- [ ] First Rust hot path: concurrent host sweep via `swarm-scan` + PyO3
- [ ] Persistent run store + replay

## License

MIT © 2026 Jacob Strokus
