from __future__ import annotations

from project_manager.registry import atomic_write_json, append_jsonl, registry_lock, registry_path, utc_now
from project_manager.work_items import WorkItemError, rebuild


def _covers(required: list[str], available: list[str]) -> bool:
    return set(required).issubset(set(available))


def plan_assignments(registry: dict, work_items: dict[str, dict] | None = None) -> list[dict]:
    items = work_items or {}
    agents = registry["runtime"].get("agents", [])
    plans = []
    for item_id in sorted(items):
        item = items[item_id]
        if item.get("status") in {"completed", "handed_off"}:
            continue
        if item.get("status") == "claimed":
            plans.append({
                "schema_version": "codex_assignment_plan_v0",
                "mode": "dry_run",
                "work_item_id": item_id,
                "candidates": [],
                "blocked_by": [{"reason": "already_claimed"}],
                "authoritative": False,
            })
            continue
        candidates = []
        blocked_by = []
        for dependency in item.get("depends_on", []):
            if items.get(dependency, {}).get("status") != "completed":
                blocked_by.append({"reason": "dependency_not_completed", "work_item_id": dependency})
        if any(block["reason"] == "dependency_not_completed" for block in blocked_by):
            plans.append({
                "schema_version": "codex_assignment_plan_v0",
                "mode": "dry_run",
                "work_item_id": item_id,
                "candidates": [],
                "blocked_by": blocked_by,
                "authoritative": False,
            })
            continue
        for agent in sorted(agents, key=lambda value: value.get("id", "")):
            if agent.get("status") not in {"project_registered", "available"}:
                blocked_by.append({"agent_id": agent.get("id"), "reason": "agent_not_available"})
                continue
            if not _covers(item.get("required_capabilities", []), agent.get("capabilities", [])):
                continue
            scopes = agent.get("scope", [])
            if scopes and not set(item.get("scope", [])).issubset(set(scopes)):
                blocked_by.append({"agent_id": agent.get("id"), "reason": "scope_mismatch"})
                continue
            candidates.append({"agent_id": agent["id"], "reason": "capabilities_and_scope_match"})
        if not candidates:
            blocked_by.append({"reason": "no_capable_agent"})
        plans.append(
            {
                "schema_version": "codex_assignment_plan_v0",
                "mode": "dry_run",
                "work_item_id": item_id,
                "candidates": candidates,
                "blocked_by": blocked_by,
                "authoritative": False,
            }
        )
    return plans


def claim(root, registry: dict, work_item_id: str, agent_id: str, execute: bool = False) -> dict:
    items = rebuild(root)
    item = items.get(work_item_id)
    if item is None:
        raise WorkItemError(f"Unknown work item: {work_item_id}")
    agent = next((value for value in registry["runtime"].get("agents", []) if value.get("id") == agent_id), None)
    if agent is None:
        raise WorkItemError(f"Unknown project agent: {agent_id}")
    if any(claim.get("work_item_id") == work_item_id for claim in registry["runtime"].get("claims", [])):
        raise WorkItemError(f"Work item already claimed: {work_item_id}")
    if not any(plan["work_item_id"] == work_item_id and any(candidate["agent_id"] == agent_id for candidate in plan["candidates"]) for plan in plan_assignments(registry, items)):
        raise WorkItemError(f"Agent cannot claim work item: {agent_id}")
    event = {"event_type": "work_item_claimed", "work_item_id": work_item_id, "agent_id": agent_id, "at": utc_now()}
    if execute:
        with registry_lock(root):
            if any(claim.get("work_item_id") == work_item_id for claim in registry["runtime"].get("claims", [])):
                raise WorkItemError(f"Work item already claimed: {work_item_id}")
            registry["runtime"]["claims"].append({"work_item_id": work_item_id, "agent_id": agent_id, "claimed_at": event["at"]})
            for candidate in registry["runtime"]["agents"]:
                if candidate.get("id") == agent_id:
                    candidate["status"] = "assigned"
            append_jsonl(root / ".codex" / "work-items.jsonl", event)
            atomic_write_json(registry_path(root), registry)
    return {"mode": "execute" if execute else "dry_run", "event": event, "authoritative": execute}
