from __future__ import annotations

import hashlib
from pathlib import Path

from project_manager.registry import ACTIVE_STATE_FILE, atomic_write_text, relative_path


def file_digest(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projection_assets(root: Path, registry: dict) -> list[dict]:
    targets = [
        registry["projections"]["agents_file"],
        registry["projections"]["memory_root"],
        registry["projections"]["skill_root"],
    ]
    assets = []
    for target in targets:
        path = root / target
        assets.append(
            {
                "target_path": target,
                "ownership": "project-owned" if path.exists() else "unmanaged",
                "current_digest": file_digest(path),
                "last_verified_at": None,
                "drift": "unknown",
            }
        )
    return assets


def render_active_state(registry: dict, work_items: dict[str, dict] | None = None) -> str:
    project = registry["project"]
    planning = registry["planning"]
    runtime = registry["runtime"]
    items = work_items or {}
    lines = [
        "# Active Project State",
        "",
        f"- Project: `{project['id']}`",
        f"- Status: `{project['status']}`",
        f"- Objective: {project['objective'] or '(not supplied)' }",
        f"- Registry schema: `{registry['schema_version']}`",
        "",
        "## Planning",
        "",
        f"- Modules: {len(planning.get('modules', []))}",
        f"- Verification surfaces: {', '.join(planning.get('verification_surfaces', [])) or '(none)'}",
        "",
        "## Runtime",
        "",
        f"- Agents discovered: {len(runtime.get('agents', []))}",
        f"- Claims: {len(runtime.get('claims', []))}",
        f"- Work items: {len(items)}",
        "",
        "This file is a projection. `.codex/registry.json` and append-only ledgers are authoritative.",
        "",
    ]
    return "\n".join(lines)


def write_active_state(root: Path, registry: dict, work_items: dict[str, dict] | None = None) -> None:
    atomic_write_text(root / ACTIVE_STATE_FILE, render_active_state(registry, work_items))
