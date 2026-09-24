"""33C-R17 API isolation contracts.

Dependency-free:
- Does not import FastAPI.
- Does not make network requests.
- Verifies API source boundaries statically.
- Verifies AssistantService converts provider failure into its
  service-level error.
"""

from __future__ import annotations

import ast
from pathlib import Path

from assistant.service import AssistantService, AssistantServiceError


ROOT = Path(__file__).resolve().parents[1]


def _function_source(name: str) -> str:
    path = ROOT / "api.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                segment = ast.get_source_segment(source, node)
                assert segment is not None
                return segment

    raise AssertionError(f"Function not found: {name}")


def test_assistant_chat_maps_service_failure_to_503():
    source = _function_source("assistant_chat")

    assert "except AssistantServiceError:" in source
    assert 'status_code=503' in source
    assert 'detail="Assistant unavailable"' in source


def test_analyze_is_llm_independent():
    source = _function_source("analyze").lower()

    assert "assistant_service" not in source
    assert "assistantservice" not in source
    assert "llm" not in source


def test_dashboard_state_is_llm_independent():
    source = _function_source("dashboard_state").lower()

    assert "assistant_service" not in source
    assert "assistantservice" not in source
    assert "llm" not in source


def test_assistant_service_normalizes_provider_failure():
    class FailingLLM:
        def generate(self, question, context):
            raise RuntimeError("simulated provider failure")

    def fake_analysis(symbol, interval, mode):
        return {
            "state": object(),
            "report": {},
        }

    service = AssistantService(
        analysis_fn=fake_analysis,
        llm=FailingLLM(),
    )

    try:
        service.answer(
            question="Why is Jaguar waiting?",
            symbol="BTCUSDT",
            interval="15m",
            mode="SWING",
        )
    except AssistantServiceError as exc:
        assert str(exc) == "Assistant LLM unavailable"
    else:
        raise AssertionError("Expected AssistantServiceError")


def test_api_source_does_not_construct_an_llm_in_analyze():
    source = (ROOT / "api.py").read_text(encoding="utf-8")
    analyze = _function_source("analyze")

    assert "assistant_service" not in analyze.lower()
    assert "LLMProviderRouter" not in analyze
    assert "GroqLLMAdapter" not in analyze


TESTS = [
    test_assistant_chat_maps_service_failure_to_503,
    test_analyze_is_llm_independent,
    test_dashboard_state_is_llm_independent,
    test_assistant_service_normalizes_provider_failure,
    test_api_source_does_not_construct_an_llm_in_analyze,
]
