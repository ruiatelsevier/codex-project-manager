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
