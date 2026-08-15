---
name: project-skill-review
description: Use when recent repository work may reveal a reusable project-local workflow, pitfall, verification pattern, or tool-usage pattern for `.agents/skills/`.
---

# Project Skill Review

Use this skill to decide whether a project-local skill should be created or updated.

## Prompt

Review the conversation above and decide whether any project-local skill should be created or updated.

Scope:

- This prompt is only for project skills.
- Project skills live under `.agents/skills/`.
- Do not update `AGENTS.md`.
- Do not update `memories/`.
- Do not save personal/global memory.
- Do not edit bundled, hub-installed, external, or protected skills.

Be selective. Create or update a project skill only when the conversation reveals a stable, repeatable workflow, pitfall, verification pattern, tool-usage pattern, or repo-specific procedure that future Codex sessions in this repository should reuse.

Target shape:

- Prefer class-level skills over one-session notes.
- Prefer updating an existing `.agents/skills/<skill>/SKILL.md` when it already covers the workflow class.
- Create a new skill only when no existing project-local skill fits.
- Skill names must describe a reusable class of work.
- Skill names must not be PR numbers, task names, feature codenames, exact error strings, or `fix-X/debug-Y/audit-Z-today` artifacts.
- Avoid a long flat list of narrow one-off skills.

Signals that warrant action:

- The user corrected a repository-specific workflow, sequence, or operating procedure.
- A repeatable debugging path, implementation technique, verification method, or tool pattern emerged.
- An existing project-local skill was used and proved incomplete, misleading, or outdated.
- A workflow is likely to recur across future sessions in this repository.

How to update:

1. If a relevant project-local skill exists, suggest patching its `SKILL.md`.
2. If the learning is detailed but secondary, suggest a support file:
   - `references/<topic>.md` for session-specific detail, error transcripts, provider quirks, or compact research notes.
   - `templates/<name>.<ext>` for reusable starter artifacts.
   - `scripts/<name>.<ext>` for deterministic commands, probes, or generators.
3. If no existing project-local skill fits, suggest a new class-level skill under `.agents/skills/<skill-name>/`.

Do not capture:

- One-off task narratives.
- Temporary environment failures such as missing binaries, fresh-install errors, path mismatches, unconfigured credentials, or uninstalled packages.
- Negative durable claims like "this tool does not work" or "browser tools are broken".
- Personal style preferences unless they directly affect how this repository's repeatable project skill should be performed.
- General project facts that belong in repository memory rather than an executable workflow.

Output rules:

- Do not write files automatically.
- Present only project-skill suggestions.
- For each reviewed session, summarize the transferable learnings in English:
  1. What problem did we solve?
  2. Which steps were repetitive and can be standardized?
  3. Which decision rules materially affected the result?
  4. What failures occurred, and what were their root causes?
  5. Which commands, scripts, or templates are worth reusing?
  6. Which details are specific to this project and should not be added to a general-purpose skill?
  7. Output the proposed reusable workflow, decision rules, failure modes, reusable scripts/templates, and a suggested `SKILL.md` draft.
- For each suggestion, include:
  - action: update existing skill, add support file, or create new skill
  - target path
  - reason
  - proposed content summary
- Ask the user what to accept.
- If no project-local skill update is warranted, say exactly: `Nothing to save.`
