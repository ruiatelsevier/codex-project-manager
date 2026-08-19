from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


SCHEMA_VERSION = "codex_project_registry_v0"
REGISTRY_FILE = ".codex/registry.json"
ACTIVE_STATE_FILE = ".codex/ACTIVE_PROJECT_STATE.md"
WORK_ITEMS_FILE = ".codex/work-items.jsonl"
EVENTS_FILE = ".codex/registry-events.jsonl"


class RegistryError(ValueError):
    """Raised when registry input is invalid or unsafe to update."""


class RegistryConflict(RegistryError):
    """Raised when an existing registry does not match the project identity."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def registry_path(root: Path) -> Path:
    return root / REGISTRY_FILE


def relative_path(root: Path, path: Path) -> str:
    root_resolved = root.resolve()
    path_resolved = path.resolve(strict=False)
    try:
        return path_resolved.relative_to(root_resolved).as_posix() or "."
    except ValueError as exc:
        raise RegistryError(f"Path escapes project root: {path}") from exc


def require_relative(value: str, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise RegistryError(f"{field} must be a project-relative path")
    return path.as_posix()


def empty_registry(
    project_id: str,
    objective: str,
    non_goals: list[str],
    planning: dict,
    agents: list[dict],
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": {
            "id": project_id,
            "status": "active",
            "root": ".",
            "objective": objective,
            "non_goals": non_goals,
        },
        "planning": planning,
        "runtime": {
            "active_state_file": ACTIVE_STATE_FILE,
            "work_items_file": WORK_ITEMS_FILE,
            "agents": agents,
            "claims": [],
        },
        "projections": {
            "agents_file": "AGENTS.md",
            "memory_root": "memories",
            "skill_root": ".agents/skills",
            "assets": [],
        },
        "provenance": {
            "last_init": {"at": utc_now(), "source": "codex-project-manager-init"},
            "last_registry_update": None,
            "source_docs": planning.get("authority_sources", []),
        },
    }


def validate_registry(registry: dict) -> None:
    if not isinstance(registry, dict) or registry.get("schema_version") != SCHEMA_VERSION:
        raise RegistryError("Unsupported or missing registry schema")
    for key in ("project", "planning", "runtime", "projections", "provenance"):
        if not isinstance(registry.get(key), dict):
            raise RegistryError(f"Registry section is missing or invalid: {key}")
    project = registry["project"]
    if not project.get("id") or project.get("root") != ".":
        raise RegistryError("Registry project identity is invalid")
    runtime = registry["runtime"]
    for field in ("active_state_file", "work_items_file"):
        require_relative(runtime.get(field, ""), f"runtime.{field}")
    for field in ("agents_file", "memory_root", "skill_root"):
        require_relative(registry["projections"].get(field, ""), f"projections.{field}")
    if not isinstance(runtime.get("agents"), list) or not isinstance(runtime.get("claims"), list):
        raise RegistryError("Registry runtime collections are invalid")


def load_registry(root: Path) -> dict | None:
    path = registry_path(root)
    if not path.exists():
        return None
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Cannot read registry safely: {path}") from exc
    validate_registry(registry)
    return registry


@contextmanager
def registry_lock(root: Path) -> Iterator[None]:
    lock_path = root / ".codex" / "registry.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_write_json(path: Path, value: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def register(root: Path, candidate: dict, active_state: str) -> dict:
    """Persist one validated registration under a single project lock."""
    root = root.resolve()
    with registry_lock(root):
        existing = load_registry(root)
        if existing is not None:
            if existing["project"]["id"] != candidate["project"]["id"]:
                raise RegistryConflict("Existing registry belongs to another project")
            if existing["project"]["objective"] != candidate["project"]["objective"]:
                raise RegistryConflict("Registration objective conflicts with existing registry")
            return {"status": "idempotent", "registry": existing}

        registry = candidate
        validate_registry(registry)
        atomic_write_json(registry_path(root), registry)
        atomic_write_text(root / ACTIVE_STATE_FILE, active_state)
        (root / WORK_ITEMS_FILE).parent.mkdir(parents=True, exist_ok=True)
        (root / WORK_ITEMS_FILE).touch(exist_ok=True)
        append_jsonl(
            root / EVENTS_FILE,
            {"event_type": "project_registered", "at": utc_now(), "project_id": registry["project"]["id"]},
        )
        return {"status": "registered", "registry": registry}
