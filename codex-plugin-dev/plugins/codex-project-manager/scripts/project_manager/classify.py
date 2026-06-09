from __future__ import annotations

from .models import CandidateKind, ReviewCandidate


PREFERENCE_MARKERS = (
    "user prefers",
    "user dislikes",
    "prefers concise",
    "communication style",
    "personal preference",
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
        return "personal_memory"
    if any(marker in haystack for marker in RULE_MARKERS):
        return "rule"
    return "knowledge"
