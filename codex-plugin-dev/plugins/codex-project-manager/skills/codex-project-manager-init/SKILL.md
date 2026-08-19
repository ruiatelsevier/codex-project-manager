---
name: codex-project-manager-init
description: Registers a Codex project after a read-only blueprint and Agent profile scan, then projects confirmed project assets.
---

# Codex Project Manager Init

Use this skill to initialize a repository for Codex Project Manager. Registration is a two-step operation: inspect and present a dry-run plan, then execute only after the user confirms the plan.

After this plugin is installed and enabled, this skill appears in the Codex slash command list. It is not a native `/cpm-init` command.

## Workflow

1. Inspect the current repository state and do not write anything:

```text
AGENTS.md
memories/
.agents/skills/
.codex/hooks.json
docs/**/*.md
$CODEX_HOME/agents/*.toml (fallback: ~/.codex/agents/*.toml)
```

2. Ask the user to confirm the project objective, non-goals, modules, authority docs, verification commands, assignment-preview setting, and which discovered Agent profiles may be registered. Discovery is not authorization.

3. Generate a registration plan:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --register --root . --objective "<confirmed objective>" --module "<confirmed module>" \
  --agent-id "<confirmed agent id>"
```

The command is dry-run by default. It must show the Registry, Blueprint, projection targets, and discovered Agent candidates. Do not create `.codex/registry.json` before confirmation.

4. After confirmation, run the same command with `--execute`.

5. Ask the user for project rules to add to `AGENTS.md`.
   - If `AGENTS.md` is missing, create it.
   - If `AGENTS.md` exists, append only missing rules to `## Codex Project Manager Rules`.
   - If the user provides no rules, skip `AGENTS.md` writes.
6. Ask whether to create optional memory module names under `memories/`.
   - Accept comma-separated or newline-separated module names.
   - Module names are project-specific components.
   - Create only `memories/<module>/`; do not create fixed topic files.
   - Long-term memory entries belong at `memories/<module>/<topic>.md` after the component and topic are clear.
   - If the user provides no modules, skip memory module creation.
7. Ensure the project-local skills directory is `.agents/skills`.
8. Ask before installing the optional hook into `.codex/hooks.json`.
   - If `.codex/hooks.json` already exists, do not overwrite it; report that manual merge is required.
9. For the legacy asset-only setup, run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "<project rule>" \
  --module "<module name>" \
  --project-skills-dir .agents/skills
```

Add `--rules` once per project rule and `--module` once per requested module. Add `--install-hook` only after the user confirms hook installation.

10. Summarize the registration result and the JSON statuses for `agents`, `memories`, `project_skills`, and `hook` when the legacy setup is also requested.
11. Do not write global or personal memory. Never overwrite existing AGENTS, memory, skill, or hook content during projection.
