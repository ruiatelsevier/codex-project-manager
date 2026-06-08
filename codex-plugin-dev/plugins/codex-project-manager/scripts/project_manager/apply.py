from __future__ import annotations

from pathlib import Path


def append_agents_rule(path: Path, rule_line: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n\n## Working Rules\n\n"
    header = "## Working Rules\n\n"
    if header not in text:
        text = text.rstrip() + "\n\n" + header
    if rule_line in text:
        path.write_text(text, encoding="utf-8")
        return
    before, after = text.split(header, 1)
    updated = before + header + after.rstrip() + "\n" + rule_line + "\n"
    path.write_text(updated, encoding="utf-8")


def append_memory_note(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        prefix = path.read_text(encoding="utf-8").rstrip() + "\n\n"
    else:
        prefix = f"# {path.stem.replace('-', ' ').title()}\n\n"
    path.write_text(prefix + f"## {title}\n\n{body}\n", encoding="utf-8")


def write_project_skill(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n\n" + body + "\n", encoding="utf-8")
        return
    path.write_text(
        "---\n"
        f"name: {path.parent.name}\n"
        f"description: {title}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
