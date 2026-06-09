from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.curate import find_memory_overlaps


def test_detects_duplicate_memory_headings(tmp_path: Path):
    mem_root = tmp_path / "memories" / "frontend"
    mem_root.mkdir(parents=True)
    (mem_root / "state.md").write_text("# State\n\n## Cache\n\nCache notes.\n", encoding="utf-8")
    (mem_root / "rendering.md").write_text("# Rendering\n\n## Cache\n\nCache notes.\n", encoding="utf-8")
    overlaps = find_memory_overlaps(tmp_path / "memories")
    assert overlaps == [("frontend/rendering.md", "frontend/state.md", "Cache")]
