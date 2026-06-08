from __future__ import annotations

SUPPORTED_TOPICS = {
    "architecture",
    "workflows",
    "pitfalls",
    "glossary",
    "decisions",
}


def normalize_module(module: str) -> str:
    value = module.strip().lower().replace("_", "-")
    if not value:
        raise ValueError("Module name is required")
    return value


def plan_memory_path(module: str, topic: str) -> str:
    module_name = normalize_module(module)
    topic_name = topic.strip().lower()
    if topic_name not in SUPPORTED_TOPICS:
        raise ValueError(f"Unsupported topic: {topic_name}")
    return f"memories/{module_name}/{topic_name}.md"
