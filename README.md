# swamAi

Build **AI swarms** — small teams of cooperating agents — for different missions:
information **search**, **intrusion detection**, and **authorized security
testing**. Agents don't message each other directly; they collaborate over a
shared **blackboard**, so you can add, remove, or re-role agents without
rewiring anything.

- **Provider-agnostic brains.** One `LLMProvider` interface; swap Claude, GPT,
  or a local Ollama model with an env var. Runs fully offline with a built-in
  mock provider (no keys, no network).
- **Python core, Rust hot paths.** Orchestration in Python for the agent
  ecosystem; a Cargo workspace (`crates/`) for performance-critical pieces,
  exposed back to Python via PyO3/maturin.
- **Pluggable capabilities.** Each mission type is a drop-in pack under
  `swarm/capabilities/`.

## Architecture

```
Mission ──► Swarm ──► [ agents run concurrently, N rounds ]
                          │        │        │
                          ▼        ▼        ▼
                        ┌──────── Blackboard ────────┐   shared state:
                        │  findings · alerts · recon │   every agent reads
                        └──────────────┬─────────────┘   peers' work each round
                                       ▼
                                 Coordinator ──► decision-ready brief
```

- **`swarm/core/`** — `Agent`, `Swarm`, `Blackboard`, `Mission`.
- **`swarm/providers/`** — `mock`, `anthropic`, `openai`, `ollama` behind one interface.
- **`swarm/capabilities/`** — `search`, `intrusion_detection`, `offensive`.

## Quick start

```bash
pip install -e ".[dev]"          # core + test deps (no keys needed)
python examples/search_swarm.py  # runs offline with the mock provider
pytest                           # all green, fully offline
```

CLI:

```bash
python -m swarm search "post-quantum key exchange"
python -m swarm ids --events sample_events.json
python -m swarm recon app.example.com --scope "*.example.com"

# Use a real model:
SWARM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-... python -m swarm search "..."
```

## Capabilities

| Pack | What it does | Status |
|------|--------------|--------|
| `search` | Agents cover different angles of a query, synthesize into one brief. Pluggable search backend. | ✅ core |
| `intrusion_detection` | Deterministic detectors (brute-force, scanner UAs, rare egress) + LLM triage to cut alert fatigue. Defensive. | ✅ core |
| `offensive` | Scope-gated reconnaissance (DNS, HTTP fingerprint) for authorized engagements. | ✅ recon |

## Responsible use

The `offensive` pack is for **reconnaissance and assessment of assets you own or
are contractually authorized to test**. Authorization is enforced *in code*:
every active action passes through `ScopeGuard`, built from the mission's
explicit `scope`. No scope → nothing active runs. The framework intentionally
**does not** include exploitation payloads, malware, or delivery mechanisms.

See [`SECURITY.md`](SECURITY.md).

## Roadmap

- [ ] LLM-driven tool calling (function-calling across providers)
- [ ] First Rust hot path: concurrent host sweep via `swarm-scan` + PyO3
- [ ] Persistent run store (`runs/`) + replay
- [ ] More detectors; sigma-rule import for the IDS pack

## License

MIT © 2026 Jacob Strokus
