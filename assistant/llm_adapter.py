"""LLM adapter for the Jaguar read-only Assistant."""

from __future__ import annotations

import json
import os
from typing import Any


class LLMAdapterError(RuntimeError):
    pass


class GroqLLMAdapter:
    def __init__(self, client: Any = None, model: str | None = None):
        self._client = client
        self._model = model or os.environ.get(
            "JAGUAR_ASSISTANT_MODEL",
            "openai/gpt-oss-120b",
        )

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMAdapterError("Groq client unavailable") from exc

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise LLMAdapterError("GROQ_API_KEY is not configured")

        self._client = Groq(api_key=api_key)
        return self._client

    def generate(self, question: str, context: dict) -> str:
        if not isinstance(question, str) or not question.strip():
            raise LLMAdapterError("Question is required")

        if not isinstance(context, dict):
            raise LLMAdapterError("Assistant context must be a dictionary")

        system_prompt = """
You are Jaguar Quant X Assistant.

You are a read-only explanation and analysis assistant.

Use ONLY the supplied canonical Jaguar context as factual trading-system
state. Do not invent missing market facts, approvals, orders, fills, positions,
or execution events.

You may explain Jaguar's current decision, market structure, risk,
execution state, and system state.

You are NOT an execution authority.
Never claim that you placed, modified, cancelled, or authorized an order.
Never instruct the user to bypass Jaguar's execution gates.

Clearly distinguish what Jaguar reports from interpretation and from unknown
information.

Be concise and professional.
""".strip()

        user_prompt = (
            "CANONICAL CONTEXT:\n"
            + json.dumps(context, indent=2, default=str)
            + "\n\nUSER QUESTION:\n"
            + question.strip()
        )

        try:
            response = self._get_client().chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )
        except Exception as exc:
            raise LLMAdapterError("LLM request failed") from exc

        try:
            reply = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise LLMAdapterError("Invalid LLM response") from exc

        if not isinstance(reply, str) or not reply.strip():
            raise LLMAdapterError("Empty LLM response")

        return reply.strip()
