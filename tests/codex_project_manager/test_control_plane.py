from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from project_manager.agent_discovery import discover_agents, register_agents, resolve_codex_home
from project_manager.blueprint import build_registration_plan
from project_manager.projections import render_active_state
from project_manager.registry import RegistryConflict, RegistryError, load_registry, register
from project_manager.registry_update import apply_update, build_update_plan
from project_manager.routing import claim, plan_assignments
from project_manager.work_items import create, rebuild


def register_test_project(tmp_path: Path, objective: str = "Build the project manager") -> dict:
    plan = build_registration_plan(tmp_path, objective=objective, environ={"CODEX_HOME": str(tmp_path / "codex-home")})
    return register(tmp_path, plan["registry"], render_active_state(plan["registry"], {}))


def test_registration_is_relative_atomic_and_idempotent(tmp_path: Path):
    first = register_test_project(tmp_path)
    second = register_test_project(tmp_path)

    assert first["status"] == "registered"
    assert second["status"] == "idempotent"
    assert load_registry(tmp_path)["project"]["root"] == "."
    assert (tmp_path / ".codex" / "ACTIVE_PROJECT_STATE.md").exists()
    assert (tmp_path / ".codex" / "registry-events.jsonl").read_text(encoding="utf-8").count("project_registered") == 1


def test_registration_conflict_fails_closed(tmp_path: Path):
    register_test_project(tmp_path, objective="one")
    plan = build_registration_plan(tmp_path, objective="two", environ={"CODEX_HOME": str(tmp_path / "codex-home")})

    try:
        register(tmp_path, plan["registry"], render_active_state(plan["registry"], {}))
    except RegistryConflict:
        pass
    else:
        raise AssertionError("conflicting registration must fail closed")


def test_corrupt_registry_fails_closed_and_existing_assets_are_preserved(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# User-owned\n", encoding="utf-8")
    register_test_project(tmp_path)
    assert agents.read_text(encoding="utf-8") == "# User-owned\n"
    (tmp_path / ".codex" / "registry.json").write_text("{broken", encoding="utf-8")

    try:
        load_registry(tmp_path)
    except RegistryError:
        pass
    else:
        raise AssertionError("corrupt registry must fail closed")


def test_agent_discovery_uses_codex_home_and_records_digest(tmp_path: Path):
    codex_home = tmp_path / "custom-codex"
    agents = codex_home / "agents"
    agents.mkdir(parents=True)
    (agents / "architect.toml").write_text(
        'name = "Software Architect"\nroles = ["architect"]\ncapabilities = ["python"]\n',
        encoding="utf-8",
    )
    result = discover_agents({"CODEX_HOME": str(codex_home)})

    assert resolve_codex_home({"CODEX_HOME": str(codex_home)}) == codex_home
    assert result["agents"][0]["id"] == "software-architect"
    assert result["agents"][0]["profile_path"] == "agents/architect.toml"
    assert len(result["agents"][0]["profile_digest"]) == 64


def test_damaged_agent_profile_is_reported_without_authorization(tmp_path: Path):
    agents = tmp_path / "codex" / "agents"
    agents.mkdir(parents=True)
    (agents / "broken.toml").write_text("name = [", encoding="utf-8")

    result = discover_agents({"CODEX_HOME": str(tmp_path / "codex")})

    assert result["agents"] == []
    assert result["errors"][0]["profile_path"] == "agents/broken.toml"


def test_agent_registration_is_explicit(tmp_path: Path):
    plan = build_registration_plan(tmp_path, environ={"CODEX_HOME": str(tmp_path / "codex-home")})
    (tmp_path / "codex-home" / "agents").mkdir(parents=True)
    profile = tmp_path / "codex-home" / "agents" / "one.toml"
    profile.write_text('name = "One"\n', encoding="utf-8")
    plan = build_registration_plan(tmp_path, environ={"CODEX_HOME": str(tmp_path / "codex-home")})
    register(tmp_path, plan["registry"], render_active_state(plan["registry"], {}))

    assert register_agents(tmp_path, ["one"], execute=False)["authoritative"] is False
    register_agents(tmp_path, ["one"], execute=True)
    assert load_registry(tmp_path)["runtime"]["agents"][0]["status"] == "project_registered"


def test_work_item_ledger_rebuild_and_assignment_are_deterministic(tmp_path: Path):
    result = register_test_project(tmp_path)
    registry = result["registry"]
    registry["runtime"]["agents"] = [
        {"id": "z-agent", "status": "project_registered", "capabilities": ["python"], "scope": ["core"]},
        {"id": "a-agent", "status": "project_registered", "capabilities": ["python"], "scope": ["core"]},
    ]
    create(
        tmp_path,
        {
            "work_item_id": "task-001",
            "title": "Implement core",
            "kind": "implementation",
            "scope": ["core"],
            "required_capabilities": ["python"],
            "write_scope": ["core"],
            "depends_on": [],
            "validation": ["focused-pytest"],
            "handoff_to": [],
        },
        execute=True,
    )
    plans = plan_assignments(registry, rebuild(tmp_path))

    assert [candidate["agent_id"] for candidate in plans[0]["candidates"]] == ["a-agent", "z-agent"]
    assert claim(tmp_path, registry, "task-001", "a-agent")["authoritative"] is False
    claim(tmp_path, registry, "task-001", "a-agent", execute=True)
    assert rebuild(tmp_path)["task-001"]["status"] == "claimed"


def test_discovered_agent_is_not_assignable_before_project_registration(tmp_path: Path):
    result = register_test_project(tmp_path)
    registry = result["registry"]
    registry["runtime"]["agents"] = [
        {"id": "discovered", "status": "discovered", "capabilities": ["python"], "scope": ["core"]}
    ]
    create(
        tmp_path,
        {
            "work_item_id": "task-002",
            "title": "Needs authorization",
            "kind": "implementation",
            "scope": ["core"],
            "required_capabilities": ["python"],
            "write_scope": ["core"],
            "depends_on": [],
            "validation": [],
            "handoff_to": [],
        },
        execute=True,
    )

    assert plan_assignments(registry, rebuild(tmp_path))[0]["candidates"] == []


def test_registry_update_changes_planning_only_and_is_audited(tmp_path: Path):
    result = register_test_project(tmp_path, objective="old")
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    doc = tmp_path / "docs" / "plans" / "current.md"
    doc.write_text("# Current Plan\n\n## Objective\n\nnew\n", encoding="utf-8")
    decisions = {
        "objective": {
            "action": "use_doc",
            "value": "new",
            "source_path": "docs/plans/current.md",
            "source_heading": "## Objective",
        }
    }

    preview = build_update_plan(tmp_path, decisions)
    assert preview["authoritative"] is False
    apply_update(tmp_path, decisions)
    updated = load_registry(tmp_path)
    assert updated["project"]["objective"] == "new"
    assert updated["project"]["status"] == "active"
    assert updated["runtime"]["claims"] == result["registry"]["runtime"]["claims"]
    event = json.loads((tmp_path / ".codex" / "registry-events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert event["planning_drift"] is True

    doc.write_text("# Current Plan\n\n## Objective\n\nnewer\n", encoding="utf-8")
    changed = build_update_plan(tmp_path)
    assert changed["source_changes"]["modified"] == ["docs/plans/current.md"]
