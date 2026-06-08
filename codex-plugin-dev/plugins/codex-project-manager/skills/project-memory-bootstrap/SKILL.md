---
name: project-memory-bootstrap
description: Create the initial memories/ tree, project-local skill folder, and optional hook template for this repository.
---

# Project Memory Bootstrap

Use this skill to initialize a repository for project memory capture.

## Workflow

1. Ensure these directories exist:

```text
memories/agent-core/
memories/tools/
memories/gateway/
.codex/skills/
```

2. Ensure these files exist:

```text
memories/agent-core/architecture.md
memories/agent-core/workflows.md
memories/agent-core/pitfalls.md
memories/tools/architecture.md
memories/tools/workflows.md
memories/tools/pitfalls.md
memories/gateway/architecture.md
memories/gateway/workflows.md
memories/gateway/pitfalls.md
```

3. If the user wants semi-automatic reminders, offer to copy:

```text
codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json
```

into:

```text
.codex/hooks.json
```
