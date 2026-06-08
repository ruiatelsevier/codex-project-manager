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
        title="Run pytest before closing agent-core edits",
        summary="Future work in this repo should run the agent-core pytest subset before closing agent-core changes.",
        evidence=["User asked for repeatable verification guidance."],
    )
    result = classify_candidate(candidate)
    assert result == "rule"


def test_classifies_knowledge_candidate():
    candidate = ReviewCandidate(
        id="c2",
        title="Agent core workflow overview",
        summary="AIAgent initializes state, assembles prompt and context, then loops through model calls and tools.",
        evidence=["Thread produced an architecture explanation."],
    )
    result = classify_candidate(candidate)
    assert result == "knowledge"


def test_classifies_project_skill_candidate():
    candidate = ReviewCandidate(
        id="c3",
        title="Debug the agent loop in this repo",
        summary="To debug the agent loop here, inspect run_agent.py, agent/conversation_loop.py, and model_tools.py in that order.",
        evidence=["Thread described a repeatable task recipe."],
    )
    result = classify_candidate(candidate)
    assert result == "project_skill"


def test_classifies_global_preference_candidate():
    candidate = ReviewCandidate(
        id="c4",
        title="User prefers concise answers",
        summary="The user repeatedly asked for concise answers and dislikes verbose explanations.",
        evidence=["User explicitly asked for brevity."],
    )
    result = classify_candidate(candidate)
    assert result == "global_preference_candidate"
