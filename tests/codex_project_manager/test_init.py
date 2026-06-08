from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.init import (
    ensure_agents_file,
    ensure_memory_modules,
    ensure_project_skills_dir,
    install_hook_if_missing,
    normalize_module_name,
)


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


def test_rejects_empty_normalized_module_name():
    try:
        normalize_module_name("!!!")
    except ValueError as exc:
        assert "Module name is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty normalized module name")


def test_creates_project_skills_dir_idempotently(tmp_path: Path):
    skills_dir = tmp_path / ".agents" / "skills"

    created = ensure_project_skills_dir(skills_dir)
    skipped = ensure_project_skills_dir(skills_dir)

    assert skills_dir.is_dir()
    assert created == {"target": ".agents/skills", "status": "created"}
    assert skipped == {
        "target": ".agents/skills",
        "status": "skipped",
        "reason": "already_exists",
    }


def test_installs_hook_when_missing_and_validates_template(tmp_path: Path):
    hook_path = tmp_path / ".codex" / "hooks.json"
    template_path = tmp_path / "template-hooks.json"
    template = {"hooks": {"PostToolUse": [{"matchers": ["patch"], "command": "python3 review.py"}]}}
    template_path.write_text(json.dumps(template), encoding="utf-8")

    result = install_hook_if_missing(hook_path, template_path)

    assert json.loads(hook_path.read_text(encoding="utf-8")) == template
    assert result == {"target": ".codex/hooks.json", "status": "created"}


def test_refuses_to_overwrite_existing_hook(tmp_path: Path):
    hook_path = tmp_path / ".codex" / "hooks.json"
    template_path = tmp_path / "template-hooks.json"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text('{"existing": true}', encoding="utf-8")
    template_path.write_text('{"hooks": {}}', encoding="utf-8")

    result = install_hook_if_missing(hook_path, template_path)

    assert hook_path.read_text(encoding="utf-8") == '{"existing": true}'
    assert result == {
        "target": ".codex/hooks.json",
        "status": "needs_manual_merge",
        "reason": "already_exists",
    }


def test_rejects_invalid_hook_template(tmp_path: Path):
    hook_path = tmp_path / ".codex" / "hooks.json"
    template_path = tmp_path / "template-hooks.json"
    template_path.write_text("{invalid json", encoding="utf-8")

    result = install_hook_if_missing(hook_path, template_path)

    assert not hook_path.exists()
    assert result["target"] == ".codex/hooks.json"
    assert result["status"] == "error"
    assert result["reason"] == "invalid_template_json"
    assert "error" in result


def test_cli_prints_json_summary(tmp_path: Path):
    root = tmp_path / "project"
    template_path = tmp_path / "template-hooks.json"
    template_path.write_text('{"hooks": {"PostToolUse": []}}', encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_SCRIPTS / "project_manager" / "init.py"),
            "--root",
            str(root),
            "--rules",
            "Run focused tests",
            "--module",
            "Frontend App",
            "--project-skills-dir",
            ".agents/skills",
            "--install-hook",
            "--hook-template",
            str(template_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(completed.stdout)
    assert summary["agents"]["status"] == "created"
    assert summary["memories"]["modules"] == ["frontend-app"]
    assert summary["project_skills"] == {"target": ".agents/skills", "status": "created"}
    assert summary["hook"] == {"target": ".codex/hooks.json", "status": "created"}
