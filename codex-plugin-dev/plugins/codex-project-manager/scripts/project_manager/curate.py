from __future__ import annotations

import json
import re
from pathlib import Path

HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
TOPIC_PRIORITY = {
    "workflows.md": 0,
    "architecture.md": 1,
    "pitfalls.md": 2,
}


def find_memory_overlaps(memories_root: Path) -> list[tuple[str, str, str]]:
    files = sorted(
        memories_root.rglob("*.md"),
        key=lambda path: (path.parent.as_posix(), TOPIC_PRIORITY.get(path.name, 99), path.name),
    )
    indexed: dict[str, list[str]] = {}
    for file_path in files:
        rel = file_path.relative_to(memories_root).as_posix()
        text = file_path.read_text(encoding="utf-8")
        for heading in HEADING_RE.findall(text):
            indexed.setdefault(heading.strip(), []).append(rel)

    overlaps = []
    for heading, paths in indexed.items():
        if len(paths) > 1:
            first, second = paths[0], paths[1]
            overlaps.append((first, second, heading))
    return overlaps


def main() -> int:
    root = Path("memories")
    if not root.exists():
        print(json.dumps({"overlaps": []}, indent=2))
        return 0
    print(json.dumps({"overlaps": find_memory_overlaps(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
