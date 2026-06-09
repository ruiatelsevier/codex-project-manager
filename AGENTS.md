# AGENTS.md

## Working Rules


- Run focused pytest before closing agent-core edits

## Codex Project Manager Rules

- Expose initialization through the `codex-project-manager-init` slash-searchable skill entry, not as a native `/cpm-init` command.
- During initialization, create `AGENTS.md` only when it is missing. If it exists, append only a bounded project-manager section.
- Ask the user for project rules before adding them to `AGENTS.md`.
- Treat all concrete `memories/<module>/` names as project-specific examples, not a fixed required module framework.
- Create memory module directories only for module names confirmed by the user. Modules may also be created later.
- Create `.agents/skills/` only if missing.
- Ask before installing `.codex/hooks.json`; never overwrite an existing hook file by default.
- In memory review, separate project rules, project knowledge, and personal memory. Suggest project rules for `AGENTS.md`, project knowledge for `memories/<module>/<topic>.md`, and save personal memory only after explicit user approval.
