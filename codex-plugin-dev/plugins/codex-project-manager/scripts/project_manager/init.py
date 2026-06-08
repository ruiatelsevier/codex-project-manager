from __future__ import annotations

import re
from pathlib import Path

MEMORY_TOPICS = ("architecture", "workflows", "pitfalls")


def normalize_rule(rule: str) -> str:
    value = rule.strip()
    if not value:
        return ""
    if value.startswith("- "):
        return value
    return f"- {value}"


def normalize_module_name(module: str) -> str:
    value = module.strip().lower().replace("_", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9-]+", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Module name is required")
    return value


def topic_title(topic: str) -> str:
    return topic.title()


def starter_memory_content(topic: str) -> str:
    return (
        f"# {topic_title(topic)}\n"
        "\n"
        "## Initial Notes\n"
        "\n"
        f"This file stores durable {topic} knowledge for this module.\n"
    )


def ensure_agents_file(path: Path, rules: list[str]) -> dict[str, object]:
    normalized_rules = [rule for rule in (normalize_rule(rule) for rule in rules) if rule]
    if not normalized_rules:
        return {
            "target": path.name,
            "status": "skipped",
            "reason": "no_rules",
            "rules_added": [],
        }

    if not path.exists():
        path.write_text(
            "# AGENTS.md\n"
            "\n"
            "## Working Rules\n"
            "\n"
            + "\n".join(normalized_rules)
            + "\n",
            encoding="utf-8",
        )
        return {
            "target": path.name,
            "status": "created",
            "rules_added": normalized_rules,
        }

    text = path.read_text(encoding="utf-8")
    rules_to_add = [rule for rule in normalized_rules if rule not in text]
    if not rules_to_add:
        return {
            "target": path.name,
            "status": "skipped",
            "reason": "rules_already_present",
            "rules_added": [],
        }

    separator = "" if text.endswith("\n") else "\n"
    addition = (
        f"{separator}\n"
        "## Codex Project Manager Rules\n"
        "\n"
        + "\n".join(rules_to_add)
        + "\n"
    )
    path.write_text(text + addition, encoding="utf-8")
    return {
        "target": path.name,
        "status": "updated",
        "rules_added": rules_to_add,
    }


def ensure_memory_modules(memories_root: Path, modules: list[str]) -> dict[str, object]:
    module_names = []
    for module in modules:
        module_name = normalize_module_name(module)
        if module_name and module_name not in module_names:
            module_names.append(module_name)

    if not module_names:
        return {
            "target": memories_root.name,
            "status": "skipped",
            "reason": "no_modules",
            "modules": [],
            "created": [],
            "skipped": [],
        }

    created = []
    skipped = []
    for module_name in module_names:
        module_root = memories_root / module_name
        module_root.mkdir(parents=True, exist_ok=True)
        for topic in MEMORY_TOPICS:
            topic_path = module_root / f"{topic}.md"
            rel_path = f"{module_name}/{topic}.md"
            if topic_path.exists():
                skipped.append(rel_path)
                continue
            topic_path.write_text(starter_memory_content(topic), encoding="utf-8")
            created.append(rel_path)

    return {
        "target": memories_root.name,
        "status": "created" if created else "skipped",
        "modules": module_names,
        "created": created,
        "skipped": skipped,
    }
