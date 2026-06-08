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
