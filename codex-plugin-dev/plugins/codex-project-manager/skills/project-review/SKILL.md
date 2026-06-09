---
name: project-review
description: Use when a work stage appears complete, including when the user says "任务完成", "task complete", or "done", and durable project memory may need review.
---

# Project Review

Use this skill when a work stage appears complete and you need to decide whether any durable memory should be saved.

Trigger this skill before finalizing when the user says a completion phrase such as:

- `任务完成`
- `task complete`
- `done`
- `finished`
- `this stage is complete`

## Memory Review Prompt

Review the conversation above and decide whether any durable memory should be saved.

Focus only on information that is stable, useful for future work, and explicitly supported by the conversation.

Classify candidates into these buckets:

1. Project rule
   - Repository-specific instructions, conventions, verification commands, or operating rules.
   - Do not save these to global memory.
   - Suggest adding them to `AGENTS.md`.

2. Project knowledge
   - Durable facts about this repository's architecture, workflows, pitfalls, or decisions.
   - Do not save these to global memory.
   - Suggest adding them to `memories/<module>/<topic>.md`.

3. Personal memory
   - User persona, preferences, working style, expectations, constraints, or personal details worth remembering across repositories.
   - Save only if it is approved by the user.
   - If appropriate, save with the memory tool.

Rules:

- Do not invent preferences or memories.
- Do not save temporary task details, one-off commands, or facts that are likely to become stale.
- Do not write project files automatically.
- If there is no personal memory worth saving and no project-memory suggestion worth presenting, say exactly: `Nothing to save.`
- If there are project-memory suggestions, present them grouped by bucket and ask the user what to accept.

## Workflow

1. Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
```

2. Group the returned suggestions into:
   - Project rule candidates for `AGENTS.md`
   - Project knowledge candidates for `memories/<module>/<topic>.md`
   - Personal memory candidates that require explicit user approval

3. Ask the user which suggestions to accept before writing anything.
