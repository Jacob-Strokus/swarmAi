import asyncio

from swarm.general import GeneralSwarm, parse_plan
from swarm.providers import get_provider


def _factory():
    return get_provider("mock")


def test_parse_plan_extracts_roles():
    text = "researcher: gather sources\ncritic: poke holes\n- writer: draft the answer"
    roles = parse_plan(text)
    assert ("researcher", "gather sources") in roles
    assert any(name == "critic" for name, _ in roles)
    assert len(roles) == 3


def test_parse_plan_caps_roles():
    text = "\n".join(f"r{i}: do thing {i}" for i in range(10))
    assert len(parse_plan(text, max_roles=4)) == 4


def test_general_swarm_falls_back_and_runs_offline():
    # The mock planner returns no parseable roles, so the fallback team runs.
    swarm = GeneralSwarm(_factory, rounds=1)
    result = asyncio.run(swarm.run("explain lattice-based cryptography simply"))
    assert result["report"]
    assert result["plan"]  # a team was assembled
    # fallback team = solver + critic => 2 agents x 1 round + coordinator summary
    assert len(result["entries"]) == 2 * 1 + 1
