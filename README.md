# codex-project-manager

Codex Project Manager is a local Codex plugin for preserving repository rules,
project memory, and project-local skills. It keeps durable project guidance in
plain files:

- `AGENTS.md` for repository rules.
- `memories/` for module knowledge.
- `.agents/skills` for project-local skills.
- `.codex/hooks.json` for the optional review hook.

## Repository Layout

### Script Tree

```text
codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/
+-- __init__.py
+-- apply.py
+-- classify.py
+-- curate.py
+-- init.py
+-- memory_paths.py
+-- models.py
`-- review.py
```

### Skill Tree

```text
codex-plugin-dev/plugins/codex-project-manager/skills/
+-- codex-project-manager-init/
|   `-- SKILL.md
+-- project-curate/
|   `-- SKILL.md
+-- project-memory-bootstrap/
|   `-- SKILL.md
`-- project-review/
    `-- SKILL.md
```

## Requirements

- Codex CLI with plugin marketplace support.
- Python 3.9 or newer.
- `pytest` for running tests.

The plugin scripts use only the Python standard library at runtime.

## Install The Plugin

Run from the repository root:

```bash
codex plugin marketplace add ./codex-plugin-dev
```

Then open Codex and install or enable `Project Manager` from the `Repo Local`
marketplace. The current CLI manages marketplaces; plugin enablement happens in
the Codex plugin UI.

Validate local plugin assets:

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json >/dev/null
```

Run tests:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/codex_project_manager -q
```

## Core Workflows

### 1. Initialize A Repository

Use `codex-project-manager-init` to prepare a repository for Codex Project
Manager. After the plugin is installed and enabled, open the Codex slash command
list and search for `codex-project-manager-init`. This is not a native platform command named `/cpm-init`.

The skill prompts for:

- Project rules to add to `AGENTS.md`.
- Optional memory module names to create under `memories/`.
- Whether to install the optional `.codex/hooks.json` review hook.

Default behavior is conservative:

- Empty rules skip `AGENTS.md` writes.
- Empty module input skips memory module creation.
- Project-local skills are created under `.agents/skills`.
- The hook is skipped unless requested.
- Existing `.codex/hooks.json` is not overwritten; the script reports that a
  manual merge is required.

Script reference:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "Run focused pytest before closing agent-core edits" \
  --module agent-core \
  --project-skills-dir .agents/skills \
  --install-hook
```

Local smoke test:

```bash
ROOT="$(mktemp -d)"
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --root "$ROOT" \
  --rules "Run focused pytest before closing agent-core edits" \
  --module agent-core \
  --project-skills-dir .agents/skills \
  --install-hook
test -f "$ROOT/AGENTS.md"
test -f "$ROOT/memories/agent-core/architecture.md"
test -f "$ROOT/memories/agent-core/workflows.md"
test -f "$ROOT/memories/agent-core/pitfalls.md"
test -d "$ROOT/.agents/skills"
test -f "$ROOT/.codex/hooks.json"
```

CLI options:

- `--rules`: project rule to write; repeat for multiple rules.
- `--module`: project module to initialize under `memories/`; repeat for multiple modules.
- `--project-skills-dir`: project skill directory, defaults to `.agents/skills`.
- `--install-hook`: install `.codex/hooks.json` from the template if it does not already exist.
- `--root`: target repository root, defaults to the current directory.

### 2. Bootstrap Project Memory

Use `project-memory-bootstrap` when a repository already has clear module names
and needs starter memory files. Bootstrap writes module knowledge under
`memories/<module>/` and keeps project-local skill discussion pointed at
`.agents/skills`.

### 3. Review Finished Work

Use `project-review` after an implementation pass to detect candidate updates
for `AGENTS.md`, `memories/`, or `.agents/skills`. Review suggestions are
advisory; apply only the updates that are relevant to the repository.

### 4. Curate Existing Knowledge

Use `project-curate` to inspect existing project memory and local skills for
stale or duplicate guidance. Keep curation surgical: edit only the files needed
for the current repository state.
