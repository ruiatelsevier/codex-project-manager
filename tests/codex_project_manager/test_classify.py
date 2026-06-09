from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "codex-plugin-dev" / "plugins" / "codex-project-manager" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_manager.classify import classify_candidate
from project_manager.models import ReviewCandidate


def test_classifies_rule_candidate():
    candidate = ReviewCandidate(
        id="c1",
        title="Run pytest before closing frontend edits",
        summary="Future work in this repo should run the frontend pytest subset before closing frontend changes.",
        evidence=["User asked for repeatable verification guidance."],
    )
    result = classify_candidate(candidate)
    assert result == "rule"


def test_classifies_knowledge_candidate():
    candidate = ReviewCandidate(
        id="c2",
        title="Frontend state workflow overview",
        summary="The frontend state cache is invalidated after successful saves.",
        evidence=["Thread produced an architecture explanation."],
    )
    result = classify_candidate(candidate)
    assert result == "knowledge"


def test_classifies_repeatable_workflow_as_knowledge_candidate():
    candidate = ReviewCandidate(
        id="c3",
        title="Debug frontend state in this repo",
        summary="To debug frontend state here, inspect the state store, save handler, and cache invalidation path in that order.",
        evidence=["Thread described a repeatable task recipe."],
    )
    result = classify_candidate(candidate)
    assert result == "knowledge"


def test_classifies_personal_memory_candidate():
    candidate = ReviewCandidate(
        id="c4",
        title="User prefers concise answers",
        summary="The user repeatedly asked for concise answers and dislikes verbose explanations.",
        evidence=["User explicitly asked for brevity."],
    )
    result = classify_candidate(candidate)
    assert result == "personal_memory"
