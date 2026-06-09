---
name: project-memory-locations
description: Use when deciding where durable component-specific project memory should be stored in `memories/<module>/<topic>.md`.
---

# Project Memory Locations

Use this skill when deciding where to save durable project knowledge for a component.

## Workflow

1. Identify the component the knowledge belongs to.
   - Use the repository's actual component or module boundary.
   - Do not infer a complete memory tree before components are clear.
   - Do not treat any prior example module names as a required framework.
2. Choose a topic filename that describes the durable knowledge:

```text
memories/<module>/<topic>.md
```

3. If the component directory does not exist yet, ask the user before creating it.
4. If the topic is unclear, suggest 1-3 concrete topic names and ask the user to choose.
5. Keep memory files scoped:
   - Project rules belong in `AGENTS.md`.
   - Repeatable project-local procedures belong in `.agents/skills/`.
   - Personal/global preferences require explicit user approval before saving.

Do not bootstrap a fixed memory layout. The full `memories/` structure emerges as the repository's components and durable topics become clear.
