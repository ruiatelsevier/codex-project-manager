# Codex Project Manager Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `codex-project-manager-init` plugin skill that appears in Codex slash search and initializes `AGENTS.md`, `memories/`, `.agents/skills/`, and optional `.codex/hooks.json` without overwriting existing files.

**Architecture:** The skill owns the conversational workflow and calls a deterministic Python stdlib CLI. `init.py` owns idempotent file operations and JSON summary output. Tests exercise the Python functions and CLI directly; README documents slash-list usage rather than a native `/cpm-init`.

**Tech Stack:** Codex plugin skills, Python 3 stdlib, pytest, Markdown docs.

---

## File Structure

Create:

```text
codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py
codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md
tests/codex_project_manager/test_init.py
```

Modify:

```text
README.md
```

Responsibilities:

- `init.py`: deterministic, idempotent initialization helpers plus CLI summary output.
- `codex-project-manager-init/SKILL.md`: slash-searchable skill workflow for collecting user choices and calling `init.py`.
- `test_init.py`: TDD coverage for AGENTS writes, memory module creation, `.agents/skills/`, hook installation, and CLI summary output.
- `README.md`: installation/use tutorial updated with the new init workflow and `.agents/skills/` path.

---

### Task 1: Add failing tests for AGENTS.md and memory module initialization

**Files:**
- Create: `tests/codex_project_manager/test_init.py`
- Create later: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py`
- Test: `.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q`

- [ ] **Step 1: Write the failing init tests**

Create `tests/codex_project_manager/test_init.py` with:

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.init import ensure_agents_file, ensure_memory_modules


def test_creates_agents_file_with_working_rules(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"

    result = ensure_agents_file(agents, ["Run focused tests before closing plugin edits"])

    assert result == {
        "target": "AGENTS.md",
        "status": "created",
        "rules_added": ["- Run focused tests before closing plugin edits"],
    }
    assert agents.read_text(encoding="utf-8") == (
        "# AGENTS.md\n\n"
        "## Working Rules\n\n"
        "- Run focused tests before closing plugin edits\n"
    )


def test_appends_bounded_section_when_agents_exists(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Existing\n\n## Notes\n\nKeep this content.\n", encoding="utf-8")

    result = ensure_agents_file(
        agents,
        [
            "Run focused tests before closing plugin edits",
            "Keep memory updates project-local",
        ],
    )

    text = agents.read_text(encoding="utf-8")
    assert result["status"] == "updated"
    assert result["rules_added"] == [
        "- Run focused tests before closing plugin edits",
        "- Keep memory updates project-local",
    ]
    assert "# Existing" in text
    assert "## Notes\n\nKeep this content." in text
    assert "## Codex Project Manager Rules" in text
    assert "- Run focused tests before closing plugin edits" in text
    assert "- Keep memory updates project-local" in text


def test_does_not_duplicate_existing_agents_rules(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "# Existing\n\n"
        "## Codex Project Manager Rules\n\n"
        "- Run focused tests before closing plugin edits\n",
        encoding="utf-8",
    )

    result = ensure_agents_file(
        agents,
        [
            "Run focused tests before closing plugin edits",
            "Keep memory updates project-local",
        ],
    )

    text = agents.read_text(encoding="utf-8")
    assert result["status"] == "updated"
    assert result["rules_added"] == ["- Keep memory updates project-local"]
    assert text.count("- Run focused tests before closing plugin edits") == 1
    assert text.count("- Keep memory updates project-local") == 1


def test_skips_agents_file_when_rules_empty(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"

    result = ensure_agents_file(agents, ["", "   "])

    assert result == {
        "target": "AGENTS.md",
        "status": "skipped",
        "reason": "no_rules",
        "rules_added": [],
    }
    assert not agents.exists()


def test_creates_memory_topic_files_for_user_modules(tmp_path: Path):
    result = ensure_memory_modules(tmp_path / "memories", ["Frontend App", "api_service"])

    assert result["status"] == "created"
    assert result["modules"] == ["frontend-app", "api-service"]
    assert result["created"] == [
        "frontend-app/architecture.md",
        "frontend-app/workflows.md",
        "frontend-app/pitfalls.md",
        "api-service/architecture.md",
        "api-service/workflows.md",
        "api-service/pitfalls.md",
    ]
    assert (tmp_path / "memories" / "frontend-app" / "architecture.md").read_text(encoding="utf-8") == (
        "# Architecture\n\n"
        "## Initial Notes\n\n"
        "This file stores durable architecture knowledge for this module.\n"
    )


def test_skips_memory_creation_without_modules(tmp_path: Path):
    result = ensure_memory_modules(tmp_path / "memories", [])

    assert result == {
        "target": "memories",
        "status": "skipped",
        "reason": "no_modules",
        "modules": [],
        "created": [],
        "skipped": [],
    }
    assert not (tmp_path / "memories").exists()
```

- [ ] **Step 2: Run tests to verify the module is missing**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'project_manager.init'`.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/codex_project_manager/test_init.py
git commit -m "test: define project manager init behavior"
```

---

### Task 2: Implement init core helpers

**Files:**
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py`
- Test: `.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q`

- [ ] **Step 1: Add the init core implementation**

Create `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py` with:

```python
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TOPICS = ("architecture", "workflows", "pitfalls")
BOUNDED_RULES_HEADER = "## Codex Project Manager Rules"


def normalize_rule(rule: str) -> str:
    value = rule.strip()
    if not value:
        return ""
    if value.startswith("- "):
        return value
    return f"- {value}"


def normalize_module_name(module: str) -> str:
    value = module.strip().lower().replace("_", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9-]+", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Module name is required")
    return value


def topic_title(topic: str) -> str:
    return topic.replace("-", " ").title()


def starter_memory_content(topic: str) -> str:
    return (
        f"# {topic_title(topic)}\n\n"
        "## Initial Notes\n\n"
        f"This file stores durable {topic} knowledge for this module.\n"
    )


def ensure_agents_file(path: Path, rules: list[str]) -> dict[str, Any]:
    normalized_rules = [line for line in (normalize_rule(rule) for rule in rules) if line]
    if not normalized_rules:
        return {
            "target": path.name,
            "status": "skipped",
            "reason": "no_rules",
            "rules_added": [],
        }

    if not path.exists():
        path.write_text(
            "# AGENTS.md\n\n"
            "## Working Rules\n\n"
            + "\n".join(normalized_rules)
            + "\n",
            encoding="utf-8",
        )
        return {
            "target": path.name,
            "status": "created",
            "rules_added": normalized_rules,
        }

    text = path.read_text(encoding="utf-8")
    additions = [rule for rule in normalized_rules if rule not in text]
    if not additions:
        return {
            "target": path.name,
            "status": "skipped",
            "reason": "rules_already_present",
            "rules_added": [],
        }

    if BOUNDED_RULES_HEADER not in text:
        updated = text.rstrip() + f"\n\n{BOUNDED_RULES_HEADER}\n\n" + "\n".join(additions) + "\n"
    else:
        before, after = text.split(BOUNDED_RULES_HEADER, 1)
        updated = before + BOUNDED_RULES_HEADER + after.rstrip() + "\n" + "\n".join(additions) + "\n"

    path.write_text(updated, encoding="utf-8")
    return {
        "target": path.name,
        "status": "updated",
        "rules_added": additions,
    }


def ensure_memory_modules(root: Path, modules: list[str]) -> dict[str, Any]:
    if not modules:
        return {
            "target": root.name,
            "status": "skipped",
            "reason": "no_modules",
            "modules": [],
            "created": [],
            "skipped": [],
        }

    normalized_modules = []
    for module in modules:
        module_name = normalize_module_name(module)
        if module_name not in normalized_modules:
            normalized_modules.append(module_name)

    created: list[str] = []
    skipped: list[str] = []
    for module_name in normalized_modules:
        module_dir = root / module_name
        module_dir.mkdir(parents=True, exist_ok=True)
        for topic in TOPICS:
            target = module_dir / f"{topic}.md"
            rel = f"{module_name}/{topic}.md"
            if target.exists():
                skipped.append(rel)
                continue
            target.write_text(starter_memory_content(topic), encoding="utf-8")
            created.append(rel)

    return {
        "target": root.name,
        "status": "created" if created else "skipped",
        "modules": normalized_modules,
        "created": created,
        "skipped": skipped,
    }
```

- [ ] **Step 2: Run Task 1 tests**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q
```

Expected: PASS with `6 passed`.

- [ ] **Step 3: Run all existing tests**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager -q
```

Expected: PASS with `14 passed`.

- [ ] **Step 4: Commit the core helpers**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py tests/codex_project_manager/test_init.py
git commit -m "feat: add project manager init core helpers"
```

---

### Task 3: Add project skill directory, hook installation, and CLI summary

**Files:**
- Modify: `tests/codex_project_manager/test_init.py`
- Modify: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py`
- Test: `.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q`
- Smoke: `python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py --rules "Run focused tests" --module frontend`

- [ ] **Step 1: Extend tests for `.agents/skills/`, hook behavior, and CLI**

Append to `tests/codex_project_manager/test_init.py`:

```python
import json
import subprocess

from project_manager.init import (
    ensure_project_skills_dir,
    install_hook_if_missing,
)


def test_creates_agents_skills_directory_idempotently(tmp_path: Path):
    skills_dir = tmp_path / ".agents" / "skills"

    first = ensure_project_skills_dir(skills_dir)
    second = ensure_project_skills_dir(skills_dir)

    assert first == {"target": ".agents/skills", "status": "created"}
    assert second == {"target": ".agents/skills", "status": "skipped", "reason": "already_exists"}
    assert skills_dir.is_dir()


def test_installs_hook_when_missing(tmp_path: Path):
    template = tmp_path / "template-hooks.json"
    template.write_text('{"hooks": {"PostToolUse": []}}\n', encoding="utf-8")
    hook_path = tmp_path / ".codex" / "hooks.json"

    result = install_hook_if_missing(hook_path, template)

    assert result == {"target": ".codex/hooks.json", "status": "created"}
    assert json.loads(hook_path.read_text(encoding="utf-8")) == {"hooks": {"PostToolUse": []}}


def test_refuses_to_overwrite_existing_hook(tmp_path: Path):
    template = tmp_path / "template-hooks.json"
    template.write_text('{"hooks": {"PostToolUse": []}}\n', encoding="utf-8")
    hook_path = tmp_path / ".codex" / "hooks.json"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text('{"existing": true}\n', encoding="utf-8")

    result = install_hook_if_missing(hook_path, template)

    assert result == {
        "target": ".codex/hooks.json",
        "status": "needs_manual_merge",
        "reason": "already_exists",
    }
    assert json.loads(hook_path.read_text(encoding="utf-8")) == {"existing": True}


def test_cli_prints_json_summary(tmp_path: Path):
    script = PLUGIN_SCRIPTS / "project_manager" / "init.py"
    template = tmp_path / "template-hooks.json"
    template.write_text('{"hooks": {"PostToolUse": []}}\n', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(tmp_path),
            "--rules",
            "Run focused tests",
            "--module",
            "frontend",
            "--project-skills-dir",
            ".agents/skills",
            "--install-hook",
            "--hook-template",
            str(template),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    summary = json.loads(result.stdout)
    assert summary["agents"]["status"] == "created"
    assert summary["memories"]["created"] == [
        "frontend/architecture.md",
        "frontend/workflows.md",
        "frontend/pitfalls.md",
    ]
    assert summary["project_skills"] == {"target": ".agents/skills", "status": "created"}
    assert summary["hook"] == {"target": ".codex/hooks.json", "status": "created"}
```

- [ ] **Step 2: Run tests to verify missing functions**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q
```

Expected: FAIL with `ImportError` for `ensure_project_skills_dir` or `install_hook_if_missing`.

- [ ] **Step 3: Add project skill and hook helpers**

Append to `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py`:

```python
def display_path(path: Path) -> str:
    parts = path.parts
    if ".agents" in parts:
        index = parts.index(".agents")
        return "/".join(parts[index:])
    if ".codex" in parts:
        index = parts.index(".codex")
        return "/".join(parts[index:])
    return path.as_posix()


def ensure_project_skills_dir(path: Path) -> dict[str, Any]:
    if path.exists():
        return {
            "target": display_path(path),
            "status": "skipped",
            "reason": "already_exists",
        }
    path.mkdir(parents=True, exist_ok=True)
    return {
        "target": display_path(path),
        "status": "created",
    }


def install_hook_if_missing(path: Path, template_path: Path) -> dict[str, Any]:
    if path.exists():
        return {
            "target": display_path(path),
            "status": "needs_manual_merge",
            "reason": "already_exists",
        }

    template_data = json.loads(template_path.read_text(encoding="utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(template_data, indent=2) + "\n", encoding="utf-8")
    return {
        "target": display_path(path),
        "status": "created",
    }
```

- [ ] **Step 4: Add CLI parsing and summary output**

Append below the helper functions in `init.py`:

```python
def build_summary(
    root: Path,
    rules: list[str],
    modules: list[str],
    project_skills_dir: str,
    install_hook: bool,
    hook_template: Path,
) -> dict[str, Any]:
    summary = {
        "agents": ensure_agents_file(root / "AGENTS.md", rules),
        "memories": ensure_memory_modules(root / "memories", modules),
        "project_skills": ensure_project_skills_dir(root / project_skills_dir),
        "hook": {
            "target": ".codex/hooks.json",
            "status": "skipped",
            "reason": "not_requested",
        },
    }
    if install_hook:
        summary["hook"] = install_hook_if_missing(root / ".codex" / "hooks.json", hook_template)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--rules", action="append", default=[])
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--project-skills-dir", default=".agents/skills")
    parser.add_argument("--install-hook", action="store_true")
    parser.add_argument(
        "--hook-template",
        default="codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json",
    )
    args = parser.parse_args()

    root = Path(args.root)
    summary = build_summary(
        root=root,
        rules=args.rules,
        modules=args.module,
        project_skills_dir=args.project_skills_dir,
        install_hook=args.install_hook,
        hook_template=Path(args.hook_template),
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run init tests**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q
```

Expected: PASS with `10 passed`.

- [ ] **Step 6: Run all tests**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager -q
```

Expected: PASS with `18 passed`.

- [ ] **Step 7: Run CLI smoke test without hook**

Run:

```bash
tmpdir="$(mktemp -d)"
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --root "$tmpdir" \
  --rules "Run focused tests" \
  --module frontend
```

Expected: JSON output where:

- `agents.status` is `created`
- `memories.modules` is `["frontend"]`
- `project_skills.target` is `.agents/skills`
- `hook.status` is `skipped`

- [ ] **Step 8: Commit CLI and hook behavior**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py tests/codex_project_manager/test_init.py
git commit -m "feat: add project manager init CLI"
```

---

### Task 4: Align project-skill destinations with `.agents/skills/`

**Files:**
- Create: `tests/codex_project_manager/test_review.py`
- Modify: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py`
- Test: `.venv/bin/python -m pytest tests/codex_project_manager/test_review.py -q`

- [ ] **Step 1: Write the failing review destination test**

Create `tests/codex_project_manager/test_review.py` with:

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.review import build_suggestions, demo_candidates


def test_project_skill_destination_uses_agents_skills():
    suggestions = build_suggestions(demo_candidates())

    project_skill = next(item for item in suggestions if item["kind"] == "project_skill")
    assert project_skill["destination"] == ".agents/skills/agent-core-debugging/SKILL.md"
```

- [ ] **Step 2: Run the test to verify the old destination fails**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_review.py -q
```

Expected: FAIL because `review.py` currently emits `.codex/skills/agent-core-debugging/SKILL.md`.

- [ ] **Step 3: Update the review destination**

In `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py`, change:

```python
"project_skill": ".codex/skills/agent-core-debugging/SKILL.md",
```

to:

```python
"project_skill": ".agents/skills/agent-core-debugging/SKILL.md",
```

- [ ] **Step 4: Run the focused review test**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_review.py -q
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Run all tests**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager -q
```

Expected: PASS with `19 passed`.

- [ ] **Step 6: Commit destination alignment**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py tests/codex_project_manager/test_review.py
git commit -m "feat: align project skill destination with agents skills"
```

---

### Task 5: Add the slash-searchable init skill

**Files:**
- Create: `codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md`
- Test: `test -f codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md`

- [ ] **Step 1: Write the skill file**

Create `codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md` with:

````markdown
---
name: codex-project-manager-init
description: Initialize AGENTS.md, memories, project-local .agents/skills, and optional hook reminders for a repository.
---

# Codex Project Manager Init

Use this skill when the user wants to initialize Codex Project Manager for the current repository.

This skill is intended to appear in the Codex slash command list as `codex-project-manager-init` after the plugin is installed and enabled. It is not a native `/cpm-init` platform command.

## Workflow

1. Inspect whether these paths exist:

```text
AGENTS.md
memories/
.agents/skills/
.codex/hooks.json
```

2. Ask the user for project rules to record in `AGENTS.md`.

- If `AGENTS.md` does not exist, create it.
- If `AGENTS.md` exists, append only missing rules to `## Codex Project Manager Rules`.
- If the user provides no rules, skip `AGENTS.md` writes.

3. Ask the user for optional module names.

- Accept comma-separated or newline-separated names.
- Module names are project-specific.
- If the user provides no modules, skip memory module creation.

4. Ensure `.agents/skills/` exists.

5. Ask whether to install the optional hook reminder.

- If the user says yes and `.codex/hooks.json` does not exist, install the template hook.
- If `.codex/hooks.json` exists, do not overwrite it; report that manual merge is required.

6. Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "<rule>" \
  --module "<module>" \
  --project-skills-dir ".agents/skills"
```

Add `--install-hook` only if the user confirmed hook installation.

7. Summarize the JSON output:

- created
- updated
- skipped
- needs_manual_merge

Do not write global or personal memory.
````

- [ ] **Step 2: Validate the skill file exists**

Run:

```bash
test -f codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md
```

Expected: exits `0`.

- [ ] **Step 3: Check skill metadata**

Run:

```bash
rg -n "name: codex-project-manager-init|slash command list|\\.agents/skills|--install-hook" \
  codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md
```

Expected: all four patterns appear.

- [ ] **Step 4: Commit the init skill**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/skills/codex-project-manager-init/SKILL.md
git commit -m "feat: add project manager init skill"
```

---

### Task 6: Update README and run final verification

**Files:**
- Modify: `README.md`
- Test: `.venv/bin/python -m pytest tests/codex_project_manager -q`
- Test: `python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json >/dev/null`

- [ ] **Step 1: Update README structure listing**

In `README.md`, update the repo tree so it includes:

```text
      codex-project-manager-init/SKILL.md
      project-memory-bootstrap/SKILL.md
      project-review/SKILL.md
      project-curate/SKILL.md
    scripts/project_manager/
      init.py
      apply.py
      classify.py
      curate.py
      memory_paths.py
      models.py
      review.py
```

Also update the durable context bullet from:

```markdown
- Project-local repeatable workflows in `.codex/skills/`
```

to:

```markdown
- Project-local repeatable workflows initialized under `.agents/skills/`
```

Update the review classification bullet from:

```markdown
- `project_skill`: repeatable repo-local workflows that belong in `.codex/skills/`
```

to:

```markdown
- `project_skill`: repeatable repo-local workflows that belong in `.agents/skills/`
```

- [ ] **Step 2: Add init workflow documentation**

In `README.md`, add this section before the current `### 1. Bootstrap Project Memory` section:

````markdown
### 1. Initialize A Repository

Use this after installing and enabling the plugin.

In the Codex composer, type `/`, search for `codex-project-manager-init`, and trigger the skill.

This is a slash-list skill entry, not a native platform command named `/cpm-init`.

The init workflow asks for:

- project rules for `AGENTS.md`
- optional module names for `memories/<module>/`
- whether to install the optional `.codex/hooks.json` reminder

Default behavior:

- `AGENTS.md` is created only if missing.
- Existing `AGENTS.md` files get a bounded `## Codex Project Manager Rules` section.
- `memories/<module>/architecture.md`, `workflows.md`, and `pitfalls.md` are created only for user-confirmed modules.
- `.agents/skills/` is created if missing.
- `.codex/hooks.json` is installed only after confirmation and is never overwritten.

Local smoke test:

```bash
tmpdir="$(mktemp -d)"
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --root "$tmpdir" \
  --rules "Run focused tests before closing plugin edits" \
  --module frontend
```

Expected JSON includes `agents`, `memories`, `project_skills`, and `hook` keys.
````

Renumber the following workflow headings so Bootstrap becomes `### 2`, Review becomes `### 3`, and Curate becomes `### 4`.

- [ ] **Step 3: Update script reference**

Add this section before the `review.py` reference:

````markdown
### `init.py`

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "Run focused tests" \
  --module frontend
```

- `--rules`: project rule to write; repeat for multiple rules
- `--module`: project module to initialize under `memories/`; repeat for multiple modules
- `--project-skills-dir`: project skill directory, defaults to `.agents/skills`
- `--install-hook`: install `.codex/hooks.json` from the template if it does not already exist
- `--root`: target repository root, defaults to the current directory
````

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/codex_project_manager -q
```

Expected: PASS with `19 passed`.

- [ ] **Step 5: Validate JSON files**

Run:

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json >/dev/null
python3 -m json.tool .codex/hooks.json >/dev/null
```

Expected: all commands exit `0`.

- [ ] **Step 6: Run CLI smoke test**

Run:

```bash
tmpdir="$(mktemp -d)"
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --root "$tmpdir" \
  --rules "Run focused tests" \
  --module frontend \
  --install-hook
test -f "$tmpdir/AGENTS.md"
test -f "$tmpdir/memories/frontend/architecture.md"
test -d "$tmpdir/.agents/skills"
test -f "$tmpdir/.codex/hooks.json"
```

Expected: JSON summary prints first, then all `test` commands exit `0`.

- [ ] **Step 7: Verify README contains the new entry point**

Run:

```bash
rg -n "codex-project-manager-init|\\.agents/skills|not a native platform command named `/cpm-init`" README.md
```

Expected: all three concepts appear.

- [ ] **Step 8: Commit docs and final verification**

```bash
git add README.md
git commit -m "docs: document project manager init workflow"
```

---

## Spec Coverage Check

- Slash-list entry: Task 5 creates `codex-project-manager-init` skill; Task 6 documents usage.
- No deprecated custom prompts: Task 4 explicitly documents skill entry behavior only.
- `AGENTS.md` missing/create and existing/append behavior: Tasks 1 and 2.
- User-provided rules: Tasks 1, 2, 3, and 4.
- Project-specific memory modules: Tasks 1, 2, 3, and 5.
- `.agents/skills/` creation: Tasks 3, 4, and 5.
- Optional hook without overwrite: Tasks 3, 4, and 5.
- JSON summary output: Task 3.
- README update: Task 6.
- Existing review destination alignment: Task 4.

No spec gaps remain.

## Placeholder Scan

The red-flag scan passes. All files, commands, initial test code, and implementation code are concrete.

## Type Consistency Check

The plan consistently uses:

- skill name: `codex-project-manager-init`
- script path: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py`
- project skill directory: `.agents/skills`
- bounded rules header: `## Codex Project Manager Rules`
- summary statuses: `created`, `updated`, `skipped`, `needs_manual_merge`
