from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.review import build_suggestions, demo_candidates


def test_project_skill_suggestion_uses_agents_skills_destination():
    suggestions = build_suggestions(demo_candidates())
    project_skill = next(suggestion for suggestion in suggestions if suggestion["kind"] == "project_skill")
    assert project_skill["destination"] == ".agents/skills/agent-core-debugging/SKILL.md"
