# Codex Project Manager

<p>
  <a href="README.md"><strong>English</strong></a>
  ·
  <a href="README_ZN.md"><strong>中文</strong></a>
</p>

Codex Project Manager is a repo-local Codex plugin for preserving project cognition at stage boundaries.
It helps a repository keep three kinds of durable context:

- Project rules in `AGENTS.md`
- Project knowledge in `memories/<module>/<topic>.md`
- Project-local repeatable workflows in `.agents/skills/`

The plugin is intentionally conservative. It suggests global memory candidates, but it does not write to
personal/global memory automatically. Personal memory is saved only after explicit user approval.

## What This Repo Contains

```text
codex-plugin-dev/
  .agents/plugins/marketplace.json
  plugins/codex-project-manager/
    .codex-plugin/plugin.json
    skills/
      codex-project-manager-init/SKILL.md
      project-memory-locations/SKILL.md
      project-review/SKILL.md
      project-skill-review/SKILL.md
    scripts/project_manager/
      apply.py
      classify.py
      init.py
      memory_paths.py
      models.py
      review.py
    templates/hooks.json
memories/
  <module>/
    <topic>.md
tests/codex_project_manager/
```

The only memory path convention is `memories/<module>/<topic>.md`. Choose module names from actual
repository components after those component boundaries are clear.

## Current Repo Setup

This repository is already initialized for Codex Project Manager:

- `AGENTS.md` contains the repo working rules.
- `memories/` is the root for component-specific long-term project memory.
- `.agents/skills/` exists for future project-local skills.
- `.codex/hooks.json` is installed for the optional Project Manager reminder hook.

## Requirements

- Codex CLI with plugin marketplace support
- Python 3.9 or newer
- `pytest` for running tests

No runtime Python dependencies are required for the plugin scripts. They use the Python standard library.

## Install The Plugin

Run commands from the repository root.

1. Add the repo-local marketplace:

```bash
codex plugin marketplace add ./codex-plugin-dev
```

Expected output includes:

```text
Added marketplace `repo-local`
```

2. Verify the marketplace was registered:

```bash
rg -n "repo-local|codex-plugin-dev" ~/.codex/config.toml
```

Expected output should include a `marketplaces.repo-local` entry pointing at this repo's
`codex-plugin-dev` directory.

3. Open Codex and install or enable the `Project Manager` plugin from the `Repo Local` marketplace.

The current CLI exposes marketplace management, but not a separate `codex plugin install` command.
Use the Codex plugin UI after adding the marketplace.

## Verify The Installation Files

Validate the plugin metadata:

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool .codex/hooks.json >/dev/null
```

All commands should exit with status `0`.

Run the test suite:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/codex_project_manager -q
```

Expected result:

```text
23 passed
```

## Core Workflows

### 1. Initialize A Repository

Use this after installing and enabling the plugin.

In the Codex composer, type `/`, search for `codex-project-manager-init`, and trigger the skill.
This is a slash-list skill entry.

The init workflow asks for:

- project rules for `AGENTS.md`
- optional module names for `memories/<module>/`
- whether to install the optional `.codex/hooks.json` reminder

Default behavior:

- `AGENTS.md` is created only if missing.
- Existing `AGENTS.md` files get a bounded `## Codex Project Manager Rules` section.
- `memories/<module>/` directories are created only for user-confirmed modules.
- Topic files are not pre-created; durable notes are written later as `memories/<module>/<topic>.md`.
- `.agents/skills/` is created if missing.
- `.codex/hooks.json` is installed only after confirmation and is never overwritten.

Local smoke test:

```bash
tmpdir="$(mktemp -d)"
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --root "$tmpdir" \
  --rules "Run focused tests before closing plugin edits" \
  --module frontend
```

Expected JSON includes `agents`, `memories`, `project_skills`, and `hook` keys.

### 2. Locate Project Memory

Use this when deciding where durable project knowledge should be stored.

In Codex, invoke the skill:

```text
@Project Manager decide where this project memory should be stored
```

The skill uses one path convention:

```text
memories/<module>/<topic>.md
```

Module names come from actual repository components. Topic files are created only when there is
durable knowledge to save for a clear component and topic.

### 3. Review Finished Work

Use this after a coding stage, debugging session, review thread, or architecture explanation.

In Codex, invoke:

```text
@Project Manager review this finished work and suggest project memory updates
```

The review flow classifies candidate notes into:

- `rule`: project rules that belong in `AGENTS.md`
- `knowledge`: project facts that belong in `memories/`
- `personal_memory`: user preference candidates that require explicit approval before saving

For a local smoke test, run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
```

The output is JSON:

```json
{
  "suggestions": [
    {
      "id": "r1",
      "kind": "rule",
      "destination": "AGENTS.md"
    }
  ]
}
```

The actual demo prints four suggestions covering the three review classes.

### 4. Review Project Skills

Use this after a work stage that may have revealed a reusable project-local workflow, pitfall,
verification pattern, or tool-usage pattern.

In Codex, invoke:

```text
@Project Manager review this finished work for project skill updates
```

This workflow is only for `.agents/skills/`. It does not update `AGENTS.md`, `memories/`, or
personal/global memory. It suggests one of:

- updating an existing `.agents/skills/<skill>/SKILL.md`
- adding a support file under `references/`, `templates/`, or `scripts/`
- creating a new class-level skill under `.agents/skills/<skill-name>/`

The workflow asks what to accept before writing anything.

## Optional Hook Reminder

The repo includes `.codex/hooks.json`, copied from:

```text
codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json
```

The hook runs after likely write/edit tool use and prints a low-noise reminder:

```text
Project Manager: recent file-writing activity detected. Consider running $project-review if this stage is complete.
```

You can test the hook command directly:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --detect-only
```

Expected result is the one-line reminder above.

## Script Reference

### `init.py`

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "Run focused tests" \
  --module frontend
```

- `--rules`: project rule to write; repeat for multiple rules
- `--module`: project module to initialize under `memories/`; repeat for multiple modules
- `--project-skills-dir`: project skill directory, defaults to `.agents/skills`
- `--install-hook`: install `.codex/hooks.json` from the template if it does not already exist
- `--root`: target repository root, defaults to the current directory

### `review.py`

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --detect-only
```

- `--demo`: prints example review suggestions as JSON
- `--detect-only`: prints the hook reminder and exits `0`

### `apply.py`

`apply.py` contains helper functions used after a user accepts a suggestion:

- `append_agents_rule(path, rule_line)`
- `append_memory_note(path, title, body)`
- `write_project_skill(path, title, body)`

Example:

```bash
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, "codex-plugin-dev/plugins/codex-project-manager/scripts")

from project_manager.apply import append_agents_rule, append_memory_note

append_agents_rule(Path("AGENTS.md"), "- Run focused pytest before closing frontend edits")
append_memory_note(
    Path("memories/frontend/state-model.md"),
    "State Cache",
    "The frontend state cache is invalidated after successful saves.",
)
PY
```

## Development

Run all tests:

```bash
.venv/bin/python -m pytest tests/codex_project_manager -q
```

Run focused tests:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_classify.py -q
.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q
.venv/bin/python -m pytest tests/codex_project_manager/test_memory_paths.py tests/codex_project_manager/test_apply.py -q
.venv/bin/python -m pytest tests/codex_project_manager/test_review.py -q
```

Validate JSON assets:

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json >/dev/null
python3 -m json.tool .codex/hooks.json >/dev/null
```

## Safety Model

- Suggestions are separate from writes.
- Global memory candidates are suggestion-only.
- Project-local writes should be applied only after user confirmation.
- `AGENTS.md`, `memories/`, and `.agents/skills/` are the intended durable project surfaces.
