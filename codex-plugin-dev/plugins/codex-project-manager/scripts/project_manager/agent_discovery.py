from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Mapping

from project_manager.registry import EVENTS_FILE, atomic_write_json, append_jsonl, load_registry, registry_lock, registry_path, utc_now

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.9 fallback
    tomllib = None


def resolve_codex_home(environ: Mapping[str, str] | None = None, home: Path | None = None) -> Path:
    env = environ or {}
    configured = env.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else (home or Path.home()) / ".codex"


def _agent_id(name: str, fallback: str) -> str:
    value = name.strip().lower() or fallback
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or fallback


def _parse_profile(path: Path) -> dict:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    data = _loads_toml(raw.decode("utf-8"))
    name = str(data.get("name", path.stem))
    roles = data.get("roles", data.get("role", []))
    if isinstance(roles, str):
        roles = [roles]
    capabilities = data.get("capabilities", [])
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    scopes = data.get("scope", data.get("scopes", []))
    if isinstance(scopes, str):
        scopes = [scopes]
    return {
        "id": _agent_id(name, path.stem),
        "source": "codex_home_agent_profile",
        "profile_path": path.relative_to(path.parents[1]).as_posix() if path.parent.name == "agents" else path.name,
        "roles": [str(value) for value in roles],
        "capabilities": [str(value) for value in capabilities],
        "scope": [str(value) for value in scopes],
        "profile_digest": digest,
        "project_registered": False,
        "status": "discovered",
    }


def _loads_toml(text: str) -> dict:
    if tomllib is not None:
        return tomllib.loads(text)
    # Python 3.9 fallback for the scalar/list metadata used by agent profiles.
    result = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+)\s*=\s*(.*)$", line.strip())
        if not match:
            continue
        key, value = match.groups()
        if value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]
        elif value.startswith("[") and value.endswith("]"):
            result[key] = [part.strip().strip('"') for part in value[1:-1].split(",") if part.strip()]
    return result


def discover_agents(environ: Mapping[str, str] | None = None, home: Path | None = None) -> dict:
    codex_home = resolve_codex_home(environ, home)
    profiles_root = codex_home / "agents"
    agents = []
    errors = []
    for path in sorted(profiles_root.glob("*.toml")):
        try:
            agents.append(_parse_profile(path))
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            errors.append({"profile_path": path.relative_to(codex_home).as_posix(), "error": str(exc)})
    return {
        "codex_home": str(codex_home),
        "profiles_root": profiles_root.as_posix(),
        "agents": agents,
        "errors": errors,
    }


def register_agents(root: Path, agent_ids: list[str], execute: bool = False) -> dict:
    registry = load_registry(root)
    if registry is None:
        raise ValueError("Project is not registered")
    known = {agent.get("id") for agent in registry["runtime"].get("agents", [])}
    unknown = sorted(set(agent_ids) - known)
    if unknown:
        raise ValueError(f"Unknown discovered Agent profile: {', '.join(unknown)}")
    if not execute:
        return {"mode": "dry_run", "agent_ids": sorted(set(agent_ids)), "authoritative": False}
    with registry_lock(root):
        registry = load_registry(root)
        assert registry is not None
        for agent in registry["runtime"]["agents"]:
            if agent["id"] in agent_ids:
                agent["project_registered"] = True
                agent["status"] = "project_registered"
        atomic_write_json(registry_path(root), registry)
        append_jsonl(root / EVENTS_FILE, {"event_type": "agents_registered", "agent_ids": sorted(set(agent_ids)), "at": utc_now()})
    return {"mode": "execute", "agent_ids": sorted(set(agent_ids)), "authoritative": True}
