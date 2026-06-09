from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Sequence
DEFAULT_HOOK_TEMPLATE = (
    "codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json"
)


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
        if module_root.exists():
            skipped.append(module_name)
            continue
        module_root.mkdir(parents=True)
        created.append(module_name)

    return {
        "target": memories_root.name,
        "status": "created" if created else "skipped",
        "modules": module_names,
        "created": created,
        "skipped": skipped,
    }


def target_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2 and parts[-2:] == (".agents", "skills"):
        return ".agents/skills"
    if len(parts) >= 2 and parts[-2:] == (".codex", "hooks.json"):
        return ".codex/hooks.json"
    return path.as_posix()


def ensure_project_skills_dir(path: Path) -> dict[str, object]:
    target = target_label(path)
    if path.exists():
        return {
            "target": target,
            "status": "skipped",
            "reason": "already_exists",
        }

    path.mkdir(parents=True)
    return {"target": target, "status": "created"}


def install_hook_if_missing(path: Path, template_path: Path) -> dict[str, object]:
    target = target_label(path)
    if path.exists():
        return {
            "target": target,
            "status": "needs_manual_merge",
            "reason": "already_exists",
        }

    try:
        template_text = template_path.read_text(encoding="utf-8")
        json.loads(template_text)
    except json.JSONDecodeError as exc:
        return {
            "target": target,
            "status": "error",
            "reason": "invalid_template_json",
            "error": str(exc),
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template_text, encoding="utf-8")
    return {"target": target, "status": "created"}


def build_summary(
    root: Path,
    rules: list[str],
    modules: list[str],
    project_skills_dir: Path,
    install_hook: bool,
    hook_template: Path,
) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    hook_result: dict[str, object]
    if install_hook:
        hook_result = install_hook_if_missing(root / ".codex" / "hooks.json", hook_template)
    else:
        hook_result = {
            "target": ".codex/hooks.json",
            "status": "skipped",
            "reason": "not_requested",
        }

    return {
        "agents": ensure_agents_file(root / "AGENTS.md", rules),
        "memories": ensure_memory_modules(root / "memories", modules),
        "project_skills": ensure_project_skills_dir(root / project_skills_dir),
        "hook": hook_result,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--rules", action="append", default=[])
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--project-skills-dir", default=".agents/skills")
    parser.add_argument("--install-hook", action="store_true")
    parser.add_argument("--hook-template", default=DEFAULT_HOOK_TEMPLATE)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_summary(
        root=Path(args.root),
        rules=args.rules,
        modules=args.module,
        project_skills_dir=Path(args.project_skills_dir),
        install_hook=args.install_hook,
        hook_template=Path(args.hook_template),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
