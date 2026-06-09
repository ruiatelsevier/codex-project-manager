from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CandidateKind = Literal[
    "rule",
    "knowledge",
    "personal_memory",
]

Confidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class ReviewCandidate:
    id: str
    title: str
    summary: str
    evidence: list[str]
    confidence: Confidence = "medium"


@dataclass(frozen=True)
class ClassifiedCandidate:
    candidate: ReviewCandidate
    kind: CandidateKind
