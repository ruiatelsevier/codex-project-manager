from __future__ import annotations

from .models import CandidateKind, ReviewCandidate


PREFERENCE_MARKERS = (
    "user prefers",
    "user dislikes",
    "prefers concise",
    "communication style",
    "personal preference",
)

SKILL_MARKERS = (
    "how to",
    "to debug",
    "to review",
    "recipe",
    "workflow for",
    "repeatable task",
)

RULE_MARKERS = (
    "future work in this repo should",
    "always run",
    "must run",
    "repo rule",
    "verification guidance",
)


def classify_candidate(candidate: ReviewCandidate) -> CandidateKind:
    haystack = f"{candidate.title}\n{candidate.summary}".lower()

    if any(marker in haystack for marker in PREFERENCE_MARKERS):
        return "global_preference_candidate"
    if any(marker in haystack for marker in SKILL_MARKERS):
        return "project_skill"
    if any(marker in haystack for marker in RULE_MARKERS):
        return "rule"
    return "knowledge"
