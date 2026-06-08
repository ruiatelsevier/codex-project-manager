from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.init import ensure_agents_file, ensure_memory_modules


def test_creates_agents_file_with_working_rules(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"

    result = ensure_agents_file(agents, ["Run focused pytest before closing agent-core edits"])

    assert agents.read_text(encoding="utf-8") == (
        "# AGENTS.md\n"
        "\n"
        "## Working Rules\n"
        "\n"
        "- Run focused pytest before closing agent-core edits\n"
    )
    assert result == {
        "target": "AGENTS.md",
        "status": "created",
        "rules_added": ["- Run focused pytest before closing agent-core edits"],
    }


def test_appends_bounded_section_when_agents_exists(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Existing\n\n## Working Rules\n\n- Keep existing rule\n", encoding="utf-8")
    rules = [
        "Run focused pytest before closing agent-core edits",
        "Keep memory updates project-local",
    ]

    result = ensure_agents_file(agents, rules)

    text = agents.read_text(encoding="utf-8")
    assert "# Existing" in text
    assert "## Working Rules\n\n- Keep existing rule" in text
    assert (
        "## Codex Project Manager Rules\n\n"
        "- Run focused pytest before closing agent-core edits\n"
        "- Keep memory updates project-local"
    ) in text
    assert result == {
        "target": "AGENTS.md",
        "status": "updated",
        "rules_added": [
            "- Run focused pytest before closing agent-core edits",
            "- Keep memory updates project-local",
        ],
    }


def test_does_not_duplicate_existing_agents_rules(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    rule = "Run focused pytest before closing agent-core edits"

    ensure_agents_file(agents, [rule])
    result = ensure_agents_file(agents, [rule])

    text = agents.read_text(encoding="utf-8")
    assert text.count(f"- {rule}") == 1
    assert result == {
        "target": "AGENTS.md",
        "status": "skipped",
        "reason": "rules_already_present",
        "rules_added": [],
    }


def test_skips_agents_file_when_rules_empty(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"

    result = ensure_agents_file(agents, ["", "   "])

    assert not agents.exists()
    assert result == {
        "target": "AGENTS.md",
        "status": "skipped",
        "reason": "no_rules",
        "rules_added": [],
    }


def test_creates_memory_topic_files_for_user_modules(tmp_path: Path):
    memories = tmp_path / "memories"

    result = ensure_memory_modules(memories, ["Frontend App", "api_service"])

    assert result == {
        "target": "memories",
        "status": "created",
        "modules": ["frontend-app", "api-service"],
        "created": [
            "frontend-app/architecture.md",
            "frontend-app/workflows.md",
            "frontend-app/pitfalls.md",
            "api-service/architecture.md",
            "api-service/workflows.md",
            "api-service/pitfalls.md",
        ],
        "skipped": [],
    }
    for module in ("frontend-app", "api-service"):
        for topic in ("architecture", "workflows", "pitfalls"):
            path = memories / module / f"{topic}.md"
            assert path.read_text(encoding="utf-8") == (
                f"# {topic.title()}\n"
                "\n"
                "## Initial Notes\n"
                "\n"
                f"This file stores durable {topic} knowledge for this module.\n"
            )


def test_skips_memory_creation_without_modules(tmp_path: Path):
    memories = tmp_path / "memories"

    result = ensure_memory_modules(memories, [])

    assert not memories.exists()
    assert result == {
        "target": "memories",
        "status": "skipped",
        "reason": "no_modules",
        "modules": [],
        "created": [],
        "skipped": [],
    }
