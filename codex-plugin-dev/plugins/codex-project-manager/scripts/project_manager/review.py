from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from project_manager.classify import classify_candidate
from project_manager.memory_paths import plan_memory_path
from project_manager.models import ReviewCandidate


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
            "project_skill": ".agents/skills/agent-core-debugging/SKILL.md",
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
