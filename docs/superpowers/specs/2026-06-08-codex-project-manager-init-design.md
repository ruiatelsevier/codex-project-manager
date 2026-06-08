# Codex Project Manager Init Design

## Goal

Add a Codex conversation entry point named `codex-project-manager-init` that users can trigger from the Codex slash command list after installing and enabling the plugin.

The command initializes project-local cognition surfaces without overwriting existing project files:

- `AGENTS.md` for project rules
- `memories/<module>/<topic>.md` for project knowledge
- `.agents/skills/` for project-local skills, using the path selected for this plugin's init workflow
- optional `.codex/hooks.json` for stage-boundary reminders

This is not a native platform slash command named `/cpm-init`. Current Codex behavior supports enabled skills appearing in the slash command list, so this design implements the entry point as a plugin skill named `codex-project-manager-init`.

## Non-Goals

- Do not use deprecated custom prompts.
- Do not write global or personal memory.
- Do not overwrite existing `AGENTS.md`, memory files, skill files, or hook files.
- Do not force fixed module names such as `agent-core`, `gateway`, or `tools`.
- Do not generate concrete project-local skill files during init.

## User Entry

After installing and enabling the plugin, the user opens the Codex composer, types `/`, searches for `codex-project-manager-init`, and triggers the skill.

The skill then runs an interactive init workflow:

1. Inspect the current repository state.
2. Ask for project rules to record.
3. Ask for optional module names.
4. Ensure `.agents/skills/` exists.
5. Ask whether to install the optional hook.
6. Show a concise init summary.

## Architecture

### Skill Layer

Create:

```text
codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md
```

The skill owns the user-facing workflow. It should:

- Explain what will be initialized.
- Ask before installing `.codex/hooks.json`.
- Ask for project rules before writing `AGENTS.md`.
- Ask for module names, while allowing the user to skip module creation.
- Call the Python init script with explicit arguments once the user confirms choices.
- Report created, updated, skipped, and needs-manual-merge items.

### Script Layer

Create:

```text
codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py
```

The script owns deterministic, testable file operations. It should expose focused functions:

- `ensure_agents_file(path, rules)`
- `ensure_memory_modules(root, modules)`
- `ensure_project_skills_dir(path)`
- `install_hook_if_missing(path, template_path)`

It must provide a CLI for the skill to call, with arguments such as:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "Run focused tests before closing plugin edits" \
  --module frontend \
  --module api \
  --install-hook
```

The CLI should print JSON summary output so the skill can report results consistently.

## File Behavior

### `AGENTS.md`

If `AGENTS.md` does not exist, create it with:

```md
# AGENTS.md

## Working Rules

- <user provided rule>
```

If `AGENTS.md` already exists, append rules into a bounded section:

```md
## Codex Project Manager Rules

- <user provided rule>
```

If the bounded section already exists, append missing rules there. Do not duplicate existing rule lines.

### `memories/`

Modules are user-provided. For each module name, create:

```text
memories/<module>/architecture.md
memories/<module>/workflows.md
memories/<module>/pitfalls.md
```

Each file should be created only if missing. Existing files are left unchanged.

Starter content:

```md
# <Topic>

## Initial Notes

This file stores durable <topic> knowledge for this module.
```

If the user provides no modules, skip memory module creation and report that modules can be added later.

### `.agents/skills/`

Create `.agents/skills/` if it does not exist. Do not create specific skill files during init.

### `.codex/hooks.json`

Install the hook only after explicit user confirmation.

If `.codex/hooks.json` does not exist, copy:

```text
codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json
```

to:

```text
.codex/hooks.json
```

If `.codex/hooks.json` already exists, do not overwrite it. Report that manual merge is required.

## Data Flow

1. User triggers `codex-project-manager-init`.
2. Skill gathers rules, module names, and hook preference.
3. Skill calls `init.py` with explicit arguments.
4. `init.py` performs idempotent file operations.
5. `init.py` returns JSON summary.
6. Skill presents the summary to the user.

## Error Handling

- Empty rule input: skip `AGENTS.md` rule writes and report no rules were added.
- Empty module list: skip memory module creation.
- Invalid module names: normalize whitespace, lowercase names, replace spaces and underscores with hyphens, and reject names that become empty.
- Existing `.codex/hooks.json`: do not overwrite; report `needs_manual_merge`.
- JSON template parse failure: stop hook installation and report the template validation error.

## Testing

Add tests under:

```text
tests/codex_project_manager/test_init.py
```

Coverage:

- Creates `AGENTS.md` when missing.
- Appends bounded section when `AGENTS.md` exists.
- Does not duplicate repeated rules.
- Creates memory topic files for user-provided modules.
- Skips module creation when no modules are provided.
- Creates `.agents/skills/` idempotently.
- Installs `.codex/hooks.json` only when missing.
- Refuses to overwrite existing `.codex/hooks.json`.

Also update README to document:

- Triggering `codex-project-manager-init` from the slash command list.
- The difference between skill slash-list entry and native `/cpm-init`.
- The initialization prompts and resulting files.

## Success Criteria

- After plugin installation, users can search `/` for `codex-project-manager-init`.
- Init creates or updates only the intended project-local files.
- Existing files are not overwritten.
- Module names are project-specific and user-confirmed.
- Tests pass with `pytest`.
- README includes installation and init usage instructions.
