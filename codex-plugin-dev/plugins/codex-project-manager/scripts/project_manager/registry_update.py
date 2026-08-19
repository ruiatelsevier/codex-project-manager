from __future__ import annotations

import hashlib
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from project_manager.projections import projection_assets
from project_manager.registry import EVENTS_FILE, RegistryError, append_jsonl, atomic_write_json, load_registry, registry_lock, registry_path, require_relative, utc_now


DECISIONS = {"use_doc", "keep_registry", "manual_edit", "defer"}
PLANNING_FIELDS = {"objective", "non_goals", "modules", "authority_sources", "routing", "verification_surfaces"}


def scan_docs(root: Path) -> list[dict]:
    results = []
    for path in sorted((root / "docs").rglob("*.md")) if (root / "docs").exists() else []:
        text = path.read_text(encoding="utf-8")
        headings = [line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")]
        results.append(
            {
                "path": path.relative_to(root).as_posix(),
                "digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "headings": headings,
                "candidate_fields": [
                    field
                    for field, terms in {
                        "objective": ("objective", "目标"),
                        "non_goals": ("non-goal", "非目标"),
                        "modules": ("module", "模块"),
                        "routing": ("routing", "分配", "路由"),
                        "verification_surfaces": ("test", "verify", "验证"),
                    }.items()
                    if any(term in text.lower() for term in terms)
                ],
            }
        )
    return results


def _apply_value(registry: dict, field: str, value) -> None:
    if field == "objective":
        registry["project"]["objective"] = value
    elif field == "non_goals":
        registry["project"]["non_goals"] = value
    elif field in {"modules", "authority_sources", "routing", "verification_surfaces"}:
        registry["planning"][field] = value
    else:
        raise RegistryError(f"Field is not docs-updatable: {field}")


def build_update_plan(root: Path, decisions: dict | None = None) -> dict:
    registry = load_registry(root)
    if registry is None:
        raise RegistryError("Project is not registered")
    docs = scan_docs(root)
    previous = {
        entry.get("path"): entry.get("digest")
        for entry in registry["provenance"].get("source_docs", [])
        if isinstance(entry, dict)
    }
    current = {doc["path"]: doc["digest"] for doc in docs}
    source_changes = {
        "added": sorted(set(current) - set(previous)),
        "modified": sorted(path for path in set(current) & set(previous) if current[path] != previous[path]),
        "deleted": sorted(set(previous) - set(current)),
    }
    decisions = decisions or {}
    changes = []
    for field, decision in decisions.items():
        if field not in PLANNING_FIELDS:
            raise RegistryError(f"Field is not docs-updatable: {field}")
        if not isinstance(decision, dict) or decision.get("action") not in DECISIONS:
            raise RegistryError(f"Invalid decision for {field}")
        source_path = decision.get("source_path")
        if source_path:
            require_relative(source_path, f"{field}.source_path")
            source_doc = next((doc for doc in docs if doc["path"] == source_path), None)
            if source_doc is None:
                raise RegistryError(f"Decision source is not in docs/**/*.md: {source_path}")
            if decision.get("source_digest") and decision["source_digest"] != source_doc["digest"]:
                raise RegistryError(f"Decision source digest is stale: {source_path}")
        changes.append(
            {
                "field": field,
                "current": registry["project"].get(field) if field in {"objective", "non_goals"} else registry["planning"].get(field),
                "candidate": decision.get("value"),
                "action": decision["action"],
                "source_path": decision.get("source_path"),
                "source_heading": decision.get("source_heading"),
                "source_digest": decision.get("source_digest"),
                "reason": decision.get("reason", ""),
            }
        )
    return {"schema_version": "codex_registry_update_plan_v0", "mode": "dry_run", "docs": docs, "source_changes": source_changes, "changes": changes, "authoritative": False}


def apply_update(root: Path, decisions: dict) -> dict:
    plan = build_update_plan(root, decisions)
    applied = []
    deferred = []
    with registry_lock(root):
        registry = load_registry(root)
        if registry is None:
            raise RegistryError("Project is not registered")
        for change in plan["changes"]:
            if change["action"] in {"use_doc", "manual_edit"}:
                if "candidate" not in change or change["candidate"] is None:
                    raise RegistryError(f"Decision needs a value: {change['field']}")
                _apply_value(registry, change["field"], change["candidate"])
                applied.append(change["field"])
            elif change["action"] == "defer":
                deferred.append(change["field"])
        registry["projections"]["assets"] = projection_assets(root, registry)
        registry["provenance"]["last_registry_update"] = {"at": utc_now(), "source": "codex-project-manager-update-registry"}
        registry["provenance"]["source_docs"] = [
            {"path": doc["path"], "digest": doc["digest"], "modified_at": doc["modified_at"]}
            for doc in plan["docs"]
        ]
        atomic_write_json(registry_path(root), registry)
        append_jsonl(
            root / EVENTS_FILE,
            {
                "event_type": "registry_updated",
                "at": utc_now(),
                "applied_fields": applied,
                "deferred_fields": deferred,
                "planning_drift": bool(applied),
                "changes": plan["changes"],
            },
        )
    return {**plan, "mode": "execute", "applied_fields": applied, "deferred_fields": deferred, "authoritative": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--decision-file")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    decisions = {}
    if args.decision_file:
        decisions = json.loads(Path(args.decision_file).read_text(encoding="utf-8"))
    result = apply_update(Path(args.root), decisions) if args.execute else build_update_plan(Path(args.root), decisions)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
