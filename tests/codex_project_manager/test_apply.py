from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.apply import append_agents_rule


def test_appends_rule_to_working_rules_section(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# AGENTS.md\n\n## Working Rules\n\n- Existing rule\n", encoding="utf-8")
    append_agents_rule(agents, "- Run focused pytest before closing frontend edits")
    text = agents.read_text(encoding="utf-8")
    assert "- Existing rule" in text
    assert "- Run focused pytest before closing frontend edits" in text
