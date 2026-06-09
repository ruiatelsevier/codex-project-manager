from __future__ import annotations

import re


def normalize_module(module: str) -> str:
    value = module.strip().lower().replace("_", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9-]+", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Module name is required")
    return value


def normalize_topic(topic: str) -> str:
    value = topic.strip().lower().replace("_", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9-]+", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Topic name is required")
    return value


def plan_memory_path(module: str, topic: str) -> str:
    module_name = normalize_module(module)
    topic_name = normalize_topic(topic)
    return f"memories/{module_name}/{topic_name}.md"
