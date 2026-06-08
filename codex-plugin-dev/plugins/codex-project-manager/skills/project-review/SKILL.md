---
name: project-review
description: Review recent project work and suggest updates for AGENTS.md, memories/, project-local skills, and global memory candidates.
---

# Project Review

Use this skill when a work stage appears complete and you want to preserve durable project knowledge.

## Workflow

1. Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
```

2. Group the returned suggestions into:
   - AGENTS.md candidates
   - memories/ candidates
   - project skill candidates
   - global memory candidates

3. Ask the user which suggestions to accept before writing anything.
