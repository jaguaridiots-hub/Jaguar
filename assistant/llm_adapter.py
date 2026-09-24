"""
Jaguar Quant X read-only Assistant LLM provider layer.

R17 contract:
- LLMProvider is the provider boundary.
- Groq remains primary.
- OpenAI-compatible provider is deterministic fallback.
- One attempt per provider. No retry hammering at the router layer.
- Provider failures are normalized.
- LLM output is explanatory only and has no execution authority.
"""

from __future__ import annotations

import json
import os
import socket
from enum import Enum
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMFailureKind(str, Enum):
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION = "AUTHENTICATION"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_RESPONSE = "INVALID_RESPONSE"


class LLMAdapterError(RuntimeError):
    """Compatibility base error for the Assistant LLM boundary."""


class LLMProviderError(LLMAdapterError):
    """Normalized failure from one concrete provider."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        kind: LLMFailureKind = LLMFailureKind.UNAVAILABLE,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.kind = kind
        self.retryable = retryable


class LLMProvider(Protocol):
    """Canonical read-only LLM provider interface."""

    name: str

    def generate(self, question: str, context: dict) -> str:
        ...


SYSTEM_PROMPT = """
You are Jaguar Quant X Assistant.

You are a read-only explanation and analysis assistant.
Use ONLY the supplied canonical Jaguar context as factual trading-system state.
Do not invent missing market facts, approvals, orders, fills, positions,
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


def _validate_inputs(question: str, context: dict) -> None:
    if not isinstance(question, str) or not question.strip():
        raise LLMAdapterError("Question is required")

    if not isinstance(context, dict):
        raise LLMAdapterError("Assistant context must be a dictionary")


def _classify_exception(exc: Exception) -> tuple[LLMFailureKind, bool]:
    status_code = getattr(exc, "status_code", None)

    if status_code == 429 or exc.__class__.__name__ in {
        "RateLimitError",
        "HTTPTooManyRequestsError",
    }:
        return LLMFailureKind.RATE_LIMIT, True

    if (
        isinstance(exc, (TimeoutError, socket.timeout))
        or "Timeout" in exc.__class__.__name__
        or "timeout" in str(exc).lower()
    ):
        return LLMFailureKind.TIMEOUT, True

    if status_code in {401, 403} or exc.__class__.__name__ in {
        "AuthenticationError",
        "PermissionDeniedError",
    }:
        return LLMFailureKind.AUTHENTICATION, False

    return LLMFailureKind.UNAVAILABLE, False


def _extract_openai_style_reply(payload: dict) -> str:
    try:
        reply = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError(
            "Invalid LLM response",
            provider="unknown",
            kind=LLMFailureKind.INVALID_RESPONSE,
            retryable=False,
        ) from exc

    if isinstance(reply, list):
        parts: list[str] = []
        for item in reply:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        reply = "".join(parts)

    if not isinstance(reply, str) or not reply.strip():
        raise LLMProviderError(
            "Empty LLM response",
            provider="unknown",
            kind=LLMFailureKind.INVALID_RESPONSE,
            retryable=False,
        )

    return reply.strip()


class GroqLLMAdapter:
    """Primary Groq provider."""

    name = "groq"

    def __init__(
        self,
        client: Any = None,
        model: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("LLM timeout must be positive")

        self._client = client
        self._model = model or os.environ.get(
            "JAGUAR_ASSISTANT_MODEL",
            "openai/gpt-oss-120b",
        )
        self.timeout = float(timeout)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMProviderError(
                "Groq client unavailable",
                provider=self.name,
                kind=LLMFailureKind.UNAVAILABLE,
                retryable=False,
            ) from exc

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise LLMProviderError(
                "GROQ_API_KEY is not configured",
                provider=self.name,
                kind=LLMFailureKind.AUTHENTICATION,
                retryable=False,
            )

        # Explicitly disable SDK retries so R17 has exactly one attempt
        # before deterministic router failover.
        self._client = Groq(
            api_key=api_key,
            timeout=self.timeout,
            max_retries=0,
        )
        return self._client

    def generate(self, question: str, context: dict) -> str:
        _validate_inputs(question, context)

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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )
        except LLMProviderError:
            raise
        except Exception as exc:
            kind, retryable = _classify_exception(exc)
            raise LLMProviderError(
                "Groq request failed",
                provider=self.name,
                kind=kind,
                retryable=retryable,
            ) from exc

        try:
            reply = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Invalid Groq response",
                provider=self.name,
                kind=LLMFailureKind.INVALID_RESPONSE,
            ) from exc

        if not isinstance(reply, str) or not reply.strip():
            raise LLMProviderError(
                "Empty Groq response",
                provider=self.name,
                kind=LLMFailureKind.INVALID_RESPONSE,
            )

        return reply.strip()


class OpenAICompatibleLLMAdapter:
    """
    Secondary provider.

    Defaults to OpenAI's API, but the base URL is configurable so the
    provider remains usable with an OpenAI-compatible endpoint.
    """

    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("LLM timeout must be positive")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get(
            "JAGUAR_ASSISTANT_FALLBACK_MODEL",
            "gpt-5.6-luna",
        )
        self.base_url = (
            base_url
            or os.environ.get(
                "JAGUAR_ASSISTANT_FALLBACK_BASE_URL",
                "https://api.openai.com/v1",
            )
        ).rstrip("/")
        self.timeout = float(timeout)

    def generate(self, question: str, context: dict) -> str:
        _validate_inputs(question, context)

        if not self.api_key:
            raise LLMProviderError(
                "OPENAI_API_KEY is not configured",
                provider=self.name,
                kind=LLMFailureKind.AUTHENTICATION,
                retryable=False,
            )

        user_prompt = (
            "CANONICAL CONTEXT:\n"
            + json.dumps(context, indent=2, default=str)
            + "\n\nUSER QUESTION:\n"
            + question.strip()
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_completion_tokens": 500,
        }

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            status = getattr(exc, "code", None)

            if status == 429:
                kind = LLMFailureKind.RATE_LIMIT
                retryable = True
            elif status in {401, 403}:
                kind = LLMFailureKind.AUTHENTICATION
                retryable = False
            elif status in {408, 504}:
                kind = LLMFailureKind.TIMEOUT
                retryable = True
            else:
                kind = LLMFailureKind.UNAVAILABLE
                retryable = False

            raise LLMProviderError(
                f"OpenAI-compatible HTTP {status}",
                provider=self.name,
                kind=kind,
                retryable=retryable,
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise LLMProviderError(
                "OpenAI-compatible request timed out",
                provider=self.name,
                kind=LLMFailureKind.TIMEOUT,
                retryable=True,
            ) from exc
        except URLError as exc:
            raise LLMProviderError(
                "OpenAI-compatible provider unavailable",
                provider=self.name,
                kind=LLMFailureKind.UNAVAILABLE,
                retryable=False,
            ) from exc
        except OSError as exc:
            raise LLMProviderError(
                "OpenAI-compatible network failure",
                provider=self.name,
                kind=LLMFailureKind.UNAVAILABLE,
                retryable=False,
            ) from exc

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LLMProviderError(
                "Invalid OpenAI-compatible response payload",
                provider=self.name,
                kind=LLMFailureKind.INVALID_RESPONSE,
            ) from exc

        try:
            return _extract_openai_style_reply(data)
        except LLMProviderError as exc:
            raise LLMProviderError(
                str(exc),
                provider=self.name,
                kind=exc.kind,
                retryable=False,
            ) from exc


class LLMProviderRouter:
    """
    Deterministic provider failover.

    Each provider receives at most one attempt per request.
    There is no backoff loop and no retry storm.
    """

    name = "router"

    def __init__(
        self,
        primary: LLMProvider | None = None,
        fallback: LLMProvider | None = None,
    ) -> None:
        self.providers = [
            primary or GroqLLMAdapter(),
            fallback or OpenAICompatibleLLMAdapter(),
        ]

    def generate(self, question: str, context: dict) -> str:
        _validate_inputs(question, context)

        failures: list[LLMProviderError] = []

        for provider in self.providers:
            try:
                return provider.generate(question, context)
            except LLMProviderError as exc:
                failures.append(exc)
            except Exception as exc:
                failures.append(
                    LLMProviderError(
                        f"{getattr(provider, 'name', 'unknown')} provider failure",
                        provider=getattr(provider, "name", "unknown"),
                        kind=LLMFailureKind.UNAVAILABLE,
                        retryable=False,
                    )
                )

        error = LLMAdapterError("All LLM providers unavailable")
        error.failures = tuple(failures)  # type: ignore[attr-defined]
        raise error


# Backward compatibility for existing imports/tests.
LLMProviderErrorBase = LLMAdapterError
