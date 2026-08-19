from __future__ import annotations

import hashlib
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path

from project_manager.agent_discovery import discover_agents
from project_manager.registry import empty_registry, relative_path


EXCLUDED_MODULES = {".git", ".codex", ".agents", "docs", "memories", "tests", "__pycache__"}


def _project_id(name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", name.lower().replace("_", "-")).strip("-") or "project"


def _git_root(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def scan_repository(root: Path) -> dict:
    root = root.resolve()
    docs = sorted(relative_path(root, path) for path in (root / "docs").rglob("*.md")) if (root / "docs").exists() else []
    modules = sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and path.name not in EXCLUDED_MODULES and not path.name.startswith(".")
    )
    verification = []
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists() or (root / "tests").exists():
        verification.append("python -m pytest tests/codex_project_manager -q")
    if (root / "package.json").exists():
        verification.append("npm test")
    return {
        "git_root": _git_root(root),
        "project_id": _project_id(root.name),
        "root": ".",
        "agents_file": (root / "AGENTS.md").exists(),
        "memory_root": (root / "memories").exists(),
        "skill_root": (root / ".agents" / "skills").exists(),
        "docs": docs,
        "modules": modules,
        "verification_candidates": verification,
        "readme_files": sorted(
            relative_path(root, path) for path in root.glob("README*.md") if path.is_file()
        ),
    }


def build_planning(scan: dict, modules: list[str] | None = None, authority_sources: list[str] | None = None) -> dict:
    chosen_modules = modules or scan["modules"] or [scan["project_id"]]
    sources = authority_sources or (["AGENTS.md"] if scan["agents_file"] else [])
    sources = list(dict.fromkeys([*sources, *scan["docs"]]))
    module_records = []
    for module in chosen_modules:
        module_id = module.strip().lower().replace("_", "-").replace(" ", "-")
        module_records.append(
            {
                "id": module_id,
                "directory": module,
                "responsibilities": [],
                "rules": [],
                "memory_topics": [],
                "project_skills": [],
                "authority_sources": sources,
                "verification": scan["verification_candidates"],
                "default_work_kinds": ["implementation", "verification"],
                "required_agent_capabilities": [],
                "projections": [
                    {
                        "target_path": "AGENTS.md",
                        "ownership": "project-owned" if scan["agents_file"] else "unmanaged",
                        "current_digest": None,
                        "last_verified_at": None,
                        "drift": "unknown",
                    },
                    {
                        "target_path": f"memories/{module_id}",
                        "ownership": "project-owned" if scan["memory_root"] else "unmanaged",
                        "current_digest": None,
                        "last_verified_at": None,
                        "drift": "unknown",
                    },
                    {
                        "target_path": f".agents/skills/{module_id}",
                        "ownership": "project-owned" if scan["skill_root"] else "unmanaged",
                        "current_digest": None,
                        "last_verified_at": None,
                        "drift": "unknown",
                    },
                ],
            }
        )
    return {
        "modules": module_records,
        "authority_sources": sources,
        "routing": [],
        "verification_surfaces": scan["verification_candidates"],
    }


def build_registration_plan(
    root: Path,
    objective: str = "",
    non_goals: list[str] | None = None,
    modules: list[str] | None = None,
    authority_sources: list[str] | None = None,
    environ: dict[str, str] | None = None,
) -> dict:
    scan = scan_repository(root)
    planning = build_planning(scan, modules, authority_sources)
    discovered = discover_agents(environ)
    registry = empty_registry(
        project_id=scan["project_id"],
        objective=objective,
        non_goals=non_goals or [],
        planning=planning,
        agents=discovered["agents"],
    )
    registry["provenance"]["source_docs"] = [
        {
            "path": path,
            "digest": hashlib.sha256((root / path).read_bytes()).hexdigest(),
            "modified_at": datetime.fromtimestamp((root / path).stat().st_mtime, timezone.utc).isoformat(),
        }
        for path in scan["docs"]
    ]
    return {
        "schema_version": "codex_registration_plan_v0",
        "mode": "dry_run",
        "scan": scan,
        "agent_discovery": discovered,
        "registry": registry,
    }
