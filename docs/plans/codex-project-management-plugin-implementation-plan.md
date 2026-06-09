# Codex Project Management Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first-release Codex plugin that captures project rules, project knowledge, and project-local skills at stage boundaries, and offers manual curation without auto-writing global personal memory.

**Architecture:** The plugin lives in an isolated repo-local Codex plugin development workspace so it does not collide with Hermes' own `plugins/` directory. The runtime core is a set of small Python stdlib scripts that classify review candidates and write approved changes into `AGENTS.md`, `memories/`, and `.codex/skills/`; Codex skills orchestrate those scripts, and a hook template provides the semi-automatic reminder path.

**Tech Stack:** Codex plugin manifest + marketplace JSON, Python 3 stdlib CLIs, Markdown assets, pytest, repo-local Codex skills, optional Codex hook template.

---

## File Structure

Implementation root:

```text
codex-plugin-dev/
  .agents/
    plugins/
      marketplace.json
  plugins/
    codex-project-manager/
      .codex-plugin/
        plugin.json
      skills/
        project-memory-bootstrap/
          SKILL.md
        project-review/
          SKILL.md
        project-curate/
          SKILL.md
      scripts/
        project_manager/
          __init__.py
          models.py
          classify.py
          memory_paths.py
          review.py
          apply.py
          curate.py
      templates/
        hooks.json
tests/
  codex_project_manager/
    test_classify.py
    test_memory_paths.py
    test_apply.py
    test_curate.py
```

Responsibilities:

- `marketplace.json`: repo-local marketplace entry so the plugin can be installed in Codex without touching personal plugin sources.
- `plugin.json`: Codex plugin metadata and asset wiring.
- `skills/project-memory-bootstrap/SKILL.md`: creates `memories/`, topic files, and optional `.codex/hooks.json` from template.
- `skills/project-review/SKILL.md`: capture flow orchestration.
- `skills/project-curate/SKILL.md`: curation flow orchestration.
- `models.py`: dataclasses and serialization helpers for review candidates and plans.
- `classify.py`: deterministic classification rules.
- `memory_paths.py`: module/topic/path planning.
- `review.py`: candidate extraction, stage-completion heuristics, and grouped suggestion output.
- `apply.py`: confirmed writes into `AGENTS.md`, `memories/`, and `.codex/skills/`.
- `curate.py`: scans existing assets and emits cleanup suggestions.
- `templates/hooks.json`: optional hook file that prints a low-noise reminder to run the review skill after likely stage completion.
- `tests/...`: narrow unit tests around classification, path planning, writes, and curation.

---

### Task 1: Scaffold the isolated plugin workspace

**Files:**
- Create: `codex-plugin-dev/.agents/plugins/marketplace.json`
- Create: `codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json`
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/__init__.py`
- Create: `codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json`
- Test: `python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json`
- Test: `python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json`

- [ ] **Step 1: Create the failing scaffold validation checks**

```bash
test -f codex-plugin-dev/.agents/plugins/marketplace.json
test -f codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json
```

Expected: both commands fail with exit code `1` because the workspace does not exist yet.

- [ ] **Step 2: Create the plugin marketplace file**

```json
{
  "name": "repo-local",
  "interface": {
    "displayName": "Repo Local"
  },
  "plugins": [
    {
      "name": "codex-project-manager",
      "source": {
        "source": "local",
        "path": "./plugins/codex-project-manager"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

- [ ] **Step 3: Create the plugin manifest**

```json
{
  "name": "codex-project-manager",
  "version": "0.1.0",
  "description": "Capture and curate project rules, knowledge, and project-local skills for Codex repositories.",
  "author": {
    "name": "Local Development",
    "email": "local@example.invalid",
    "url": "https://example.invalid"
  },
  "homepage": "https://example.invalid",
  "repository": "https://example.invalid/codex-project-manager",
  "license": "MIT",
  "keywords": [
    "codex",
    "project-management",
    "memory",
    "skills",
    "review",
    "curation"
  ],
  "skills": "./skills/",
  "interface": {
    "displayName": "Project Manager",
    "shortDescription": "Capture repo rules, knowledge, and skills",
    "longDescription": "A Codex plugin that helps preserve project rules in AGENTS.md, project knowledge in memories/, and project-local skills in .codex/skills, with review and curation workflows inspired by Hermes Agent.",
    "developerName": "Local Development",
    "category": "Productivity",
    "capabilities": [
      "Interactive",
      "Read",
      "Write"
    ],
    "websiteURL": "https://example.invalid",
    "privacyPolicyURL": "https://example.invalid/privacy",
    "termsOfServiceURL": "https://example.invalid/terms",
    "defaultPrompt": [
      "@Project Manager review this finished work and suggest project memory updates",
      "@Project Manager bootstrap project memory folders for this repo",
      "@Project Manager curate existing project memories and skills"
    ],
    "brandColor": "#2563EB",
    "screenshots": []
  }
}
```

- [ ] **Step 4: Create the package marker and hook template**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/__init__.py
"""Project manager plugin scripts package."""
```

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matchers": [
          "write_file",
          "patch",
          "edit_file"
        ],
        "command": "python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --detect-only"
      }
    ]
  }
}
```

- [ ] **Step 5: Validate the JSON files**

Run:

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json >/dev/null
```

Expected: all commands exit `0` with no output.

- [ ] **Step 6: Commit**

```bash
git add codex-plugin-dev/.agents/plugins/marketplace.json \
  codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json \
  codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/__init__.py \
  codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json
git commit -m "feat: scaffold codex project manager plugin workspace"
```

---

### Task 2: Implement the shared data model and deterministic classification core

**Files:**
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/models.py`
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/classify.py`
- Create: `tests/codex_project_manager/test_classify.py`
- Test: `python3 -m pytest tests/codex_project_manager/test_classify.py -q`

- [ ] **Step 1: Write the failing classification tests**

```python
from codex_plugin_test_import import classify_candidate, ReviewCandidate


def test_classifies_rule_candidate():
    candidate = ReviewCandidate(
        id="c1",
        title="Run pytest before closing agent-core edits",
        summary="Future work in this repo should run the agent-core pytest subset before closing agent-core changes.",
        evidence=["User asked for repeatable verification guidance."],
    )
    result = classify_candidate(candidate)
    assert result == "rule"


def test_classifies_knowledge_candidate():
    candidate = ReviewCandidate(
        id="c2",
        title="Agent core workflow overview",
        summary="AIAgent initializes state, assembles prompt and context, then loops through model calls and tools.",
        evidence=["Thread produced an architecture explanation."],
    )
    result = classify_candidate(candidate)
    assert result == "knowledge"


def test_classifies_project_skill_candidate():
    candidate = ReviewCandidate(
        id="c3",
        title="Debug the agent loop in this repo",
        summary="To debug the agent loop here, inspect run_agent.py, agent/conversation_loop.py, and model_tools.py in that order.",
        evidence=["Thread described a repeatable task recipe."],
    )
    result = classify_candidate(candidate)
    assert result == "project_skill"


def test_classifies_global_preference_candidate():
    candidate = ReviewCandidate(
        id="c4",
        title="User prefers concise answers",
        summary="The user repeatedly asked for concise answers and dislikes verbose explanations.",
        evidence=["User explicitly asked for brevity."],
    )
    result = classify_candidate(candidate)
    assert result == "global_preference_candidate"
```

- [ ] **Step 2: Run the test to verify import and implementation are missing**

Run:

```bash
python3 -m pytest tests/codex_project_manager/test_classify.py -q
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` because the classification module does not exist yet.

- [ ] **Step 3: Write the shared models**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CandidateKind = Literal[
    "rule",
    "knowledge",
    "project_skill",
    "global_preference_candidate",
]

Confidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class ReviewCandidate:
    id: str
    title: str
    summary: str
    evidence: list[str]
    confidence: Confidence = "medium"


@dataclass(frozen=True)
class ClassifiedCandidate:
    candidate: ReviewCandidate
    kind: CandidateKind
```

- [ ] **Step 4: Write the deterministic classifier**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/classify.py
from __future__ import annotations

from .models import ReviewCandidate, CandidateKind


PREFERENCE_MARKERS = (
    "user prefers",
    "user dislikes",
    "prefers concise",
    "communication style",
    "personal preference",
)

SKILL_MARKERS = (
    "how to",
    "to debug",
    "to review",
    "recipe",
    "workflow for",
    "repeatable task",
)

RULE_MARKERS = (
    "future work in this repo should",
    "always run",
    "must run",
    "repo rule",
    "verification guidance",
)


def classify_candidate(candidate: ReviewCandidate) -> CandidateKind:
    haystack = f"{candidate.title}\n{candidate.summary}".lower()

    if any(marker in haystack for marker in PREFERENCE_MARKERS):
        return "global_preference_candidate"
    if any(marker in haystack for marker in SKILL_MARKERS):
        return "project_skill"
    if any(marker in haystack for marker in RULE_MARKERS):
        return "rule"
    return "knowledge"
```

- [ ] **Step 5: Fix the test import path and rerun**

Replace the first line of `tests/codex_project_manager/test_classify.py` with:

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.classify import classify_candidate
from project_manager.models import ReviewCandidate
```

Run:

```bash
python3 -m pytest tests/codex_project_manager/test_classify.py -q
```

Expected: PASS with `4 passed`.

- [ ] **Step 6: Commit**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/models.py \
  codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/classify.py \
  tests/codex_project_manager/test_classify.py
git commit -m "feat: add review candidate model and classifier"
```

---

### Task 3: Implement path planning for `memories/` and bounded AGENTS.md writes

**Files:**
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/memory_paths.py`
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/apply.py`
- Create: `tests/codex_project_manager/test_memory_paths.py`
- Create: `tests/codex_project_manager/test_apply.py`
- Test: `python3 -m pytest tests/codex_project_manager/test_memory_paths.py tests/codex_project_manager/test_apply.py -q`

- [ ] **Step 1: Write the failing path-planning test**

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.memory_paths import plan_memory_path


def test_plans_agent_core_workflow_path():
    path = plan_memory_path(module="agent-core", topic="workflows")
    assert path == "memories/agent-core/workflows.md"


def test_rejects_unknown_topic():
    try:
        plan_memory_path(module="agent-core", topic="random-notes")
    except ValueError as exc:
        assert "Unsupported topic" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported topic")
```

- [ ] **Step 2: Write the failing bounded-write test**

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.apply import append_agents_rule


def test_appends_rule_to_working_rules_section(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# AGENTS.md\n\n## Working Rules\n\n- Existing rule\n", encoding="utf-8")
    append_agents_rule(agents, "- Run focused pytest before closing agent-core edits")
    text = agents.read_text(encoding="utf-8")
    assert "- Existing rule" in text
    assert "- Run focused pytest before closing agent-core edits" in text
```

- [ ] **Step 3: Run tests to verify the modules are missing**

Run:

```bash
python3 -m pytest tests/codex_project_manager/test_memory_paths.py tests/codex_project_manager/test_apply.py -q
```

Expected: FAIL with import errors because `memory_paths.py` and `apply.py` do not exist yet.

- [ ] **Step 4: Implement memory path planning**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/memory_paths.py
from __future__ import annotations

SUPPORTED_TOPICS = {
    "architecture",
    "workflows",
    "pitfalls",
    "glossary",
    "decisions",
}


def normalize_module(module: str) -> str:
    value = module.strip().lower().replace("_", "-")
    if not value:
        raise ValueError("Module name is required")
    return value


def plan_memory_path(module: str, topic: str) -> str:
    module_name = normalize_module(module)
    topic_name = topic.strip().lower()
    if topic_name not in SUPPORTED_TOPICS:
        raise ValueError(f"Unsupported topic: {topic_name}")
    return f"memories/{module_name}/{topic_name}.md"
```

- [ ] **Step 5: Implement bounded write helpers**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/apply.py
from __future__ import annotations

from pathlib import Path


def append_agents_rule(path: Path, rule_line: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n\n## Working Rules\n\n"
    header = "## Working Rules\n\n"
    if header not in text:
        text = text.rstrip() + "\n\n" + header
    if rule_line in text:
        path.write_text(text, encoding="utf-8")
        return
    before, after = text.split(header, 1)
    updated = before + header + after.rstrip() + "\n" + rule_line + "\n"
    path.write_text(updated, encoding="utf-8")


def append_memory_note(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        prefix = path.read_text(encoding="utf-8").rstrip() + "\n\n"
    else:
        prefix = f"# {path.stem.replace('-', ' ').title()}\n\n"
    path.write_text(prefix + f"## {title}\n\n{body}\n", encoding="utf-8")
```

- [ ] **Step 6: Run tests to verify the new helpers pass**

Run:

```bash
python3 -m pytest tests/codex_project_manager/test_memory_paths.py tests/codex_project_manager/test_apply.py -q
```

Expected: PASS with `3 passed`.

- [ ] **Step 7: Commit**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/memory_paths.py \
  codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/apply.py \
  tests/codex_project_manager/test_memory_paths.py \
  tests/codex_project_manager/test_apply.py
git commit -m "feat: add memory path planning and bounded write helpers"
```

---

### Task 4: Implement capture-flow review extraction and suggestion rendering

**Files:**
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py`
- Create: `codex-plugin-dev/plugins/codex-project-manager/skills/project-review/SKILL.md`
- Create: `codex-plugin-dev/plugins/codex-project-manager/skills/project-memory-bootstrap/SKILL.md`
- Test: `python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo`

- [ ] **Step 1: Write the failing demo invocation**

Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
```

Expected: FAIL with `No such file or directory`.

- [ ] **Step 2: Implement the review CLI**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_manager.classify import classify_candidate
from project_manager.models import ReviewCandidate
from project_manager.memory_paths import plan_memory_path


def demo_candidates() -> list[ReviewCandidate]:
    return [
        ReviewCandidate(
            id="r1",
            title="Agent-core verification guidance",
            summary="Future work in this repo should run focused pytest for agent-core edits before closing the task.",
            evidence=["A review thread identified repeated verification friction."],
        ),
        ReviewCandidate(
            id="k1",
            title="Agent core workflow",
            summary="AIAgent initializes state, assembles prompt and context, loops through model calls and tools, then updates session state.",
            evidence=["A high-level architecture explanation was produced."],
        ),
        ReviewCandidate(
            id="s1",
            title="How to debug the agent loop in this repo",
            summary="To debug the loop here, inspect run_agent.py, then agent/conversation_loop.py, then model_tools.py.",
            evidence=["A repeatable debugging method was documented."],
        ),
        ReviewCandidate(
            id="p1",
            title="User prefers concise answers",
            summary="The user explicitly asked for concise answers.",
            evidence=["The user said the answers should stay short."],
        ),
    ]


def build_suggestions(candidates: list[ReviewCandidate]) -> list[dict]:
    suggestions = []
    for candidate in candidates:
        kind = classify_candidate(candidate)
        destination = {
            "rule": "AGENTS.md",
            "knowledge": plan_memory_path("agent-core", "workflows"),
            "project_skill": ".codex/skills/agent-core-debugging/SKILL.md",
            "global_preference_candidate": "suggest-global-memory",
        }[kind]
        suggestions.append(
            {
                "id": candidate.id,
                "kind": kind,
                "title": candidate.title,
                "summary": candidate.summary,
                "destination": destination,
                "evidence": candidate.evidence,
            }
        )
    return suggestions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--detect-only", action="store_true")
    args = parser.parse_args()

    if args.detect_only:
        print("Project Manager: recent file-writing activity detected. Consider running $project-review if this stage is complete.")
        return 0

    if args.demo:
        print(json.dumps({"suggestions": build_suggestions(demo_candidates())}, indent=2))
        return 0

    parser.error("Pass --demo or --detect-only")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Author the project review skill**

```markdown
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
```

- [ ] **Step 4: Author the bootstrap skill**

```markdown
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
```

- [ ] **Step 5: Run the demo and detect-only modes**

Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --detect-only
```

Expected:

- first command prints JSON containing four grouped suggestion records
- second command prints a one-line reminder message and exits `0`

- [ ] **Step 6: Commit**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py \
  codex-plugin-dev/plugins/codex-project-manager/skills/project-review/SKILL.md \
  codex-plugin-dev/plugins/codex-project-manager/skills/project-memory-bootstrap/SKILL.md
git commit -m "feat: add capture flow review CLI and bootstrap skill"
```

---

### Task 5: Implement project-skill writes and manual curation suggestions

**Files:**
- Create: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/curate.py`
- Create: `codex-plugin-dev/plugins/codex-project-manager/skills/project-curate/SKILL.md`
- Create: `tests/codex_project_manager/test_curate.py`
- Modify: `codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/apply.py`
- Test: `python3 -m pytest tests/codex_project_manager/test_curate.py -q`

- [ ] **Step 1: Write the failing curation test**

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.curate import find_memory_overlaps


def test_detects_duplicate_memory_headings(tmp_path: Path):
    mem_root = tmp_path / "memories" / "agent-core"
    mem_root.mkdir(parents=True)
    (mem_root / "workflows.md").write_text("# Workflows\n\n## Loop\n\nAIAgent loops.\n", encoding="utf-8")
    (mem_root / "architecture.md").write_text("# Architecture\n\n## Loop\n\nAIAgent loops.\n", encoding="utf-8")
    overlaps = find_memory_overlaps(tmp_path / "memories")
    assert overlaps == [("agent-core/workflows.md", "agent-core/architecture.md", "Loop")]
```

- [ ] **Step 2: Run the test to verify curation is not implemented**

Run:

```bash
python3 -m pytest tests/codex_project_manager/test_curate.py -q
```

Expected: FAIL with import errors because `curate.py` does not exist yet.

- [ ] **Step 3: Extend apply helpers for project-local skill creation**

```python
# append this function to codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/apply.py
def write_project_skill(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n\n" + body + "\n", encoding="utf-8")
        return
    path.write_text(
        "---\n"
        f"name: {path.parent.name}\n"
        f"description: {title}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Implement the curation scanner**

```python
# codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/curate.py
from __future__ import annotations

from pathlib import Path
import re

HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def find_memory_overlaps(memories_root: Path) -> list[tuple[str, str, str]]:
    files = sorted(memories_root.rglob("*.md"))
    indexed: dict[str, list[str]] = {}
    for file_path in files:
        rel = file_path.relative_to(memories_root).as_posix()
        text = file_path.read_text(encoding="utf-8")
        for heading in HEADING_RE.findall(text):
            indexed.setdefault(heading.strip(), []).append(rel)

    overlaps = []
    for heading, paths in indexed.items():
        if len(paths) > 1:
            first, second = paths[0], paths[1]
            overlaps.append((first, second, heading))
    return overlaps
```

- [ ] **Step 5: Author the curation skill**

```markdown
---
name: project-curate
description: Review project memories and project-local skills for overlap, wrong-layer placement, and stale fragmentation.
---

# Project Curate

Use this skill when you want to manually review existing project cognition assets.

## Workflow

1. Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/curate.py
```

2. Review overlap and wrong-layer suggestions.
3. Ask the user which cleanup actions to apply.
4. Apply only confirmed merges, moves, or patches.
```

- [ ] **Step 6: Add a CLI entrypoint and rerun the test**

Replace `curate.py` with:

```python
from __future__ import annotations

from pathlib import Path
import json
import re

HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def find_memory_overlaps(memories_root: Path) -> list[tuple[str, str, str]]:
    files = sorted(memories_root.rglob("*.md"))
    indexed: dict[str, list[str]] = {}
    for file_path in files:
        rel = file_path.relative_to(memories_root).as_posix()
        text = file_path.read_text(encoding="utf-8")
        for heading in HEADING_RE.findall(text):
            indexed.setdefault(heading.strip(), []).append(rel)

    overlaps = []
    for heading, paths in indexed.items():
        if len(paths) > 1:
            first, second = paths[0], paths[1]
            overlaps.append((first, second, heading))
    return overlaps


def main() -> int:
    root = Path("memories")
    if not root.exists():
        print(json.dumps({"overlaps": []}, indent=2))
        return 0
    print(json.dumps({"overlaps": find_memory_overlaps(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run:

```bash
python3 -m pytest tests/codex_project_manager/test_curate.py -q
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/curate.py
```

Expected:

- pytest reports `1 passed`
- the CLI prints JSON with an `overlaps` list

- [ ] **Step 7: Commit**

```bash
git add codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/apply.py \
  codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/curate.py \
  codex-plugin-dev/plugins/codex-project-manager/skills/project-curate/SKILL.md \
  tests/codex_project_manager/test_curate.py
git commit -m "feat: add project skill writes and curation scanner"
```

---

### Task 6: End-to-end repo bootstrap and manual acceptance test

**Files:**
- Modify: `memories/agent-core/architecture.md`
- Modify: `memories/agent-core/workflows.md`
- Modify: `.codex/hooks.json` (optional)
- Test: plugin install and CLI/manual smoke run

- [ ] **Step 1: Bootstrap the target repository structure**

Create these exact files if they do not exist:

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

With this starter content pattern:

```md
# Workflows

## Initial Notes

This file stores durable workflow knowledge for the module.
```

- [ ] **Step 2: Optionally install the reminder hook**

Copy:

```text
codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json
```

to:

```text
.codex/hooks.json
```

Then validate:

```bash
python3 -m json.tool .codex/hooks.json >/dev/null
```

Expected: exit `0`.

- [ ] **Step 3: Register the local marketplace in Codex**

Run:

```bash
codex plugin marketplace add ./codex-plugin-dev
codex plugin marketplace list
```

Expected:

- add command succeeds
- list output includes the `repo-local` marketplace and the `codex-project-manager` plugin

- [ ] **Step 4: Run the capture flow smoke test**

Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
```

Expected: JSON output with:

- one `AGENTS.md` destination
- one `memories/...` destination
- one `.codex/skills/...` destination
- one `suggest-global-memory` destination

- [ ] **Step 5: Manually apply one knowledge note and one rule**

Use this exact Python one-liner:

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "codex-plugin-dev/plugins/codex-project-manager/scripts")
from project_manager.apply import append_agents_rule, append_memory_note
append_agents_rule(Path("AGENTS.md"), "- Run focused pytest before closing agent-core edits")
append_memory_note(Path("memories/agent-core/workflows.md"), "Agent Loop", "AIAgent assembles context, calls the model, loops through tool use, and updates session state.")
PY
```

Expected:

- `AGENTS.md` contains the new rule
- `memories/agent-core/workflows.md` contains a new `## Agent Loop` section

- [ ] **Step 6: Run the curation smoke test**

Run:

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/curate.py
```

Expected: JSON output with an `overlaps` key and exit `0`.

- [ ] **Step 7: Commit**

```bash
git add AGENTS.md memories .codex/hooks.json codex-plugin-dev
git commit -m "feat: wire codex project manager plugin into repo workflow"
```

---

## Spec Coverage Check

Spec requirements covered:

- project-only cognition boundary: Tasks 2, 4, and 5 enforce classification and suggestion-only global memory handling
- `AGENTS.md` for project rules: Tasks 3 and 6
- `memories/<module>/<topic>.md` structure: Tasks 3 and 6
- project-local skills: Tasks 4 and 5
- semi-automatic stage-boundary prompting: Tasks 1 and 4 via the hook template and `--detect-only`
- user-confirmed writes: Tasks 4 and 5 keep suggestions separate from apply helpers
- manual curation mode: Task 5

No spec gaps remain for v1 scope.

## Placeholder Scan

This plan intentionally avoids:

- `TBD`
- `TODO`
- "similar to previous task"
- unspecified file paths
- vague testing instructions

All file paths, commands, and initial code blocks are concrete.

## Type Consistency Check

The plan consistently uses:

- plugin name: `codex-project-manager`
- workspace root: `codex-plugin-dev`
- candidate kinds:
  - `rule`
  - `knowledge`
  - `project_skill`
  - `global_preference_candidate`
- memory topics:
  - `architecture`
  - `workflows`
  - `pitfalls`
  - `glossary`
  - `decisions`

No naming drift remains across tasks.
