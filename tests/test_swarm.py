import asyncio

from swarm.capabilities.intrusion_detection import build_ids_swarm, failed_login_bursts
from swarm.capabilities.offensive.scope import ScopeError, ScopeGuard
from swarm.capabilities.search import build_search_swarm
from swarm.core import Mission, Swarm
from swarm.providers import get_provider


def _factory():
    return get_provider("mock")


def test_search_swarm_runs_offline():
    agents = build_search_swarm(_factory)
    swarm = Swarm(agents, coordinator=get_provider("mock"))
    result = asyncio.run(swarm.run(Mission(objective="test topic", max_rounds=2)))
    assert result["report"]
    # 3 angles x 2 rounds + 1 coordinator summary
    assert len(result["entries"]) == 3 * 2 + 1


def test_ids_detector_fires_on_bruteforce():
    events = [{"event": "auth_fail", "src_ip": "1.2.3.4"} for _ in range(6)]
    assert failed_login_bursts(events)


def test_ids_swarm_triages():
    events = [{"event": "auth_fail", "src_ip": "9.9.9.9"} for _ in range(8)]
    agents = build_ids_swarm(_factory)
    swarm = Swarm(agents)
    result = asyncio.run(swarm.run(Mission(objective="triage", params={"events": events}, max_rounds=1)))
    assert any(e["kind"] == "alert" for e in result["entries"])


def test_scope_guard_blocks_out_of_scope():
    guard = ScopeGuard(["*.example.com", "10.0.0.0/24"])
    assert guard.allows("app.example.com")
    assert guard.allows("10.0.0.5")
    assert not guard.allows("evil.test")


def test_scope_guard_empty_refuses_everything():
    guard = ScopeGuard([])
    assert guard.is_empty
    try:
        guard.check("example.com")
    except ScopeError:
        pass
    else:
        raise AssertionError("empty scope must refuse")
