from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from project_manager.registry import load_registry
from project_manager.routing import claim, plan_assignments
from project_manager.work_items import rebuild


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview or confirm deterministic project assignments")
    parser.add_argument("--root", default=".")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--claim")
    parser.add_argument("--agent-id")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    registry = load_registry(Path(args.root))
    if registry is None:
        parser.error("Project is not registered")
    if args.claim:
        if not args.agent_id:
            parser.error("--claim requires --agent-id")
        result = claim(Path(args.root), registry, args.claim, args.agent_id, execute=args.execute)
    else:
        result = {
            "schema_version": "codex_assignment_plan_v0",
            "mode": "dry_run",
            "plans": plan_assignments(registry, rebuild(Path(args.root))),
            "authoritative": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
