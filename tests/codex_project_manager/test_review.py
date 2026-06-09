from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.review import build_suggestions, demo_candidates


def test_review_suggestions_use_memory_review_buckets():
    suggestions = build_suggestions(demo_candidates())
    kinds = {suggestion["kind"] for suggestion in suggestions}
    assert kinds == {"rule", "knowledge", "personal_memory"}


def test_personal_memory_suggestion_requires_approval_destination():
    suggestions = build_suggestions(demo_candidates())
    personal_memory = next(suggestion for suggestion in suggestions if suggestion["kind"] == "personal_memory")
    assert personal_memory["destination"] == "memory-tool-after-user-approval"
