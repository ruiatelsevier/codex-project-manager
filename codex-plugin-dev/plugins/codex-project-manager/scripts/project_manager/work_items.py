from __future__ import annotations

import json
from pathlib import Path

from project_manager.registry import WORK_ITEMS_FILE, append_jsonl, utc_now


STATUSES = {"created", "planned", "claimed", "in_progress", "blocked", "completed", "handed_off"}
TRANSITIONS = {
    "created": {"planned", "claimed", "blocked"},
    "planned": {"claimed", "blocked"},
    "claimed": {"in_progress", "blocked", "completed", "handed_off"},
    "in_progress": {"blocked", "completed", "handed_off"},
    "blocked": {"planned", "claimed", "in_progress", "completed", "handed_off"},
    "completed": set(),
    "handed_off": set(),
}


class WorkItemError(ValueError):
    pass


def read_events(root: Path) -> list[dict]:
    path = root / WORK_ITEMS_FILE
    if not path.exists():
        return []
    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WorkItemError(f"Invalid work item event at line {line_number}") from exc
        if not isinstance(event, dict) or not event.get("work_item_id"):
            raise WorkItemError(f"Invalid work item event at line {line_number}")
        events.append(event)
    return events


def rebuild(root: Path) -> dict[str, dict]:
    current: dict[str, dict] = {}
    for event in read_events(root):
        item_id = event["work_item_id"]
        if event.get("event_type") == "work_item_created":
            if item_id in current:
                raise WorkItemError(f"Duplicate work item: {item_id}")
            current[item_id] = {**event, "status": "created"}
        elif event.get("event_type") == "work_item_status_changed":
            if item_id not in current:
                raise WorkItemError(f"Status event references unknown work item: {item_id}")
            current[item_id] = {**current[item_id], "status": event["status"], "updated_at": event.get("at")}
        elif event.get("event_type") == "work_item_claimed":
            if item_id not in current:
                raise WorkItemError(f"Claim references unknown work item: {item_id}")
            current[item_id] = {**current[item_id], "status": "claimed", "claimed_by": event["agent_id"]}
        else:
            raise WorkItemError(f"Unknown work item event type: {event.get('event_type')}")
    return current


def create(root: Path, item: dict, execute: bool = False) -> dict:
    required = {"work_item_id", "title", "kind", "scope", "required_capabilities", "write_scope", "validation"}
    missing = sorted(required - item.keys())
    if missing:
        raise WorkItemError(f"Missing work item fields: {', '.join(missing)}")
    event = {"event_type": "work_item_created", **item, "created_at": item.get("created_at", utc_now())}
    if not execute:
        return {"mode": "dry_run", "event": event, "authoritative": False}
    rebuild(root)
    append_jsonl(root / WORK_ITEMS_FILE, event)
    return {"mode": "execute", "event": event, "authoritative": True}


def change_status(root: Path, work_item_id: str, status: str, execute: bool = False) -> dict:
    if status not in STATUSES:
        raise WorkItemError(f"Unknown work item status: {status}")
    current = rebuild(root)
    item = current.get(work_item_id)
    if item is None:
        raise WorkItemError(f"Unknown work item: {work_item_id}")
    if status not in TRANSITIONS[item["status"]]:
        raise WorkItemError(f"Invalid transition: {item['status']} -> {status}")
    event = {
        "event_type": "work_item_status_changed",
        "work_item_id": work_item_id,
        "from_status": item["status"],
        "status": status,
        "at": utc_now(),
    }
    if execute:
        append_jsonl(root / WORK_ITEMS_FILE, event)
    return {"mode": "execute" if execute else "dry_run", "event": event, "authoritative": execute}
