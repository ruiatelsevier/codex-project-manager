from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.memory_paths import plan_memory_path


def test_plans_module_topic_path():
    path = plan_memory_path(module="frontend_app", topic="state model")
    assert path == "memories/frontend-app/state-model.md"


def test_rejects_empty_topic():
    try:
        plan_memory_path(module="frontend", topic=" ")
    except ValueError as exc:
        assert "Topic name is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty topic")


def test_rejects_empty_module():
    try:
        plan_memory_path(module="!!!", topic="state")
    except ValueError as exc:
        assert "Module name is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty module")
