---
name: codex-project-manager-update-registry
description: Reconciles project planning from docs/**/*.md into the registered project Registry with field-level human decisions.
---

# Codex Project Manager Update Registry

Use this skill after a long multi-turn planning period when project docs may contain a newer plan than the initial registration.

## Workflow

1. Confirm `.codex/registry.json` exists. If it does not, run `codex-project-manager-init` first.
2. Scan all `docs/**/*.md` and generate a dry-run report:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/registry_update.py \
  --root .
```

3. Review each candidate against the current Registry. The report includes path, heading, digest, and candidate field hints. Do not infer authority from file timestamps.
4. Prepare a decision JSON whose top-level keys are planning fields and whose action is one of `use_doc`, `keep_registry`, `manual_edit`, or `defer`:

```json
{
  "objective": {
    "action": "use_doc",
    "value": "The confirmed current objective",
    "source_path": "docs/plans/current.md",
    "source_heading": "## Objective",
    "source_digest": "...",
    "reason": "Latest approved plan"
  }
}
```

`manual_edit` also requires an explicit `value`. `keep_registry` and `defer` preserve the planning value; they are still recorded for audit.

5. Execute only after the user confirms the field-level decisions:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/registry_update.py \
  --root . --decision-file /path/to/decisions.json --execute
```

The update changes only planning fields and projection provenance. It never changes project runtime status, Agent identity, claims, leases, completed work, or event history. A planning change is recorded with `planning_drift`; it does not cancel or reassign work.
