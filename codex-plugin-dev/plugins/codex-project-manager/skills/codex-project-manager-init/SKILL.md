---
name: codex-project-manager-init
description: Initializes AGENTS.md, confirmed memory module directories, .agents/skills, and an optional hook.
---

# Codex Project Manager Init

Use this skill to initialize a repository for Codex Project Manager.

After this plugin is installed and enabled, this skill appears in the Codex slash command list. It is not a native `/cpm-init` command.

## Workflow

1. Inspect the current repository state:

```text
AGENTS.md
memories/
.agents/skills/
.codex/hooks.json
```

2. Ask the user for project rules to add to `AGENTS.md`.
   - If `AGENTS.md` is missing, create it.
   - If `AGENTS.md` exists, append only missing rules to `## Codex Project Manager Rules`.
   - If the user provides no rules, skip `AGENTS.md` writes.
3. Ask whether to create optional memory module names under `memories/`.
   - Accept comma-separated or newline-separated module names.
   - Module names are project-specific components.
   - Create only `memories/<module>/`; do not create fixed topic files.
   - Long-term memory entries belong at `memories/<module>/<topic>.md` after the component and topic are clear.
   - If the user provides no modules, skip memory module creation.
4. Ensure the project-local skills directory is `.agents/skills`.
5. Ask before installing the optional hook into `.codex/hooks.json`.
   - If `.codex/hooks.json` already exists, do not overwrite it; report that manual merge is required.
6. Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "<project rule>" \
  --module "<module name>" \
  --project-skills-dir .agents/skills
```

Add `--rules` once per project rule and `--module` once per requested module. Add `--install-hook` only after the user confirms hook installation.

7. Summarize the JSON statuses for `agents`, `memories`, `project_skills`, and `hook`.
8. Do not write global or personal memory.
