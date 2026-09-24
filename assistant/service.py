"""Jaguar Assistant orchestration boundary."""

from __future__ import annotations

from typing import Any, Callable

from assistant.context import build_assistant_context
from assistant.llm_adapter import GroqLLMAdapter, LLMAdapterError
from core.jaguar_analysis_engine import JaguarAnalysisEngine
from core.kernel import JaguarKernel


class AssistantServiceError(RuntimeError):
    pass


def _default_analysis(symbol: str, interval: str, mode: str):
    kernel = JaguarKernel()
    kernel.initialize(symbol, interval)

    state = kernel.get_state()
    state.mode = mode

    result = JaguarAnalysisEngine(kernel).run(symbol)

    if not isinstance(result, dict):
        raise AssistantServiceError(
            "Canonical analysis returned invalid result"
        )

    return result


class AssistantService:
    def __init__(
        self,
        analysis_fn: Callable[[str, str, str], dict] | None = None,
        llm: Any = None,
    ):
        self._analysis_fn = analysis_fn or _default_analysis
        self._llm = llm or GroqLLMAdapter()

    def answer(
        self,
        question: str,
        symbol: str,
        interval: str,
        mode: str,
    ) -> str:
        if not isinstance(question, str) or not question.strip():
            raise AssistantServiceError("Question is required")

        try:
            result = self._analysis_fn(
                str(symbol).strip(),
                str(interval).strip(),
                str(mode).strip(),
            )

            context = build_assistant_context(
                result["state"],
                result["report"],
            )
        except AssistantServiceError:
            raise
        except Exception as exc:
            raise AssistantServiceError(
                "Canonical assistant context unavailable"
            ) from exc

        try:
            return self._llm.generate(
                question=question,
                context=context,
            )
        except LLMAdapterError as exc:
            raise AssistantServiceError(
                "Assistant LLM unavailable"
            ) from exc
        except Exception as exc:
            raise AssistantServiceError(
                "Assistant LLM unavailable"
            ) from exc
