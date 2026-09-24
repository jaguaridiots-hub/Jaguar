"""33C-R17 LLM provider resilience contracts."""

from assistant.llm_adapter import (
    LLMAdapterError,
    LLMFailureKind,
    LLMProviderError,
    LLMProviderRouter,
)


class SuccessProvider:
    name = "fallback"

    def __init__(self, reply="fallback-reply"):
        self.reply = reply
        self.calls = 0

    def generate(self, question, context):
        self.calls += 1
        return self.reply


class FailingProvider:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind
        self.calls = 0

    def generate(self, question, context):
        self.calls += 1
        raise LLMProviderError(
            f"{self.name} failed",
            provider=self.name,
            kind=self.kind,
        )


def test_429_fails_over_once():
    primary = FailingProvider("groq", LLMFailureKind.RATE_LIMIT)
    fallback = SuccessProvider()

    router = LLMProviderRouter(primary=primary, fallback=fallback)

    assert router.generate("question", {}) == "fallback-reply"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_timeout_fails_over_once():
    primary = FailingProvider("groq", LLMFailureKind.TIMEOUT)
    fallback = SuccessProvider()

    router = LLMProviderRouter(primary=primary, fallback=fallback)

    assert router.generate("question", {}) == "fallback-reply"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_provider_failure_falls_back():
    primary = FailingProvider("groq", LLMFailureKind.UNAVAILABLE)
    fallback = SuccessProvider("openai-fallback")

    router = LLMProviderRouter(primary=primary, fallback=fallback)

    assert router.generate("question", {}) == "openai-fallback"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_all_provider_failure_is_normalized():
    primary = FailingProvider("groq", LLMFailureKind.RATE_LIMIT)
    fallback = FailingProvider(
        "openai",
        LLMFailureKind.UNAVAILABLE,
    )

    router = LLMProviderRouter(primary=primary, fallback=fallback)

    try:
        router.generate("question", {})
    except LLMAdapterError as exc:
        assert str(exc) == "All LLM providers unavailable"
        failures = getattr(exc, "failures")
        assert len(failures) == 2
        assert failures[0].provider == "groq"
        assert failures[0].kind == LLMFailureKind.RATE_LIMIT
        assert failures[1].provider == "openai"
    else:
        raise AssertionError("Expected normalized all-provider failure")


def test_no_retry_hammering():
    primary = FailingProvider("groq", LLMFailureKind.RATE_LIMIT)
    fallback = FailingProvider("openai", LLMFailureKind.TIMEOUT)

    router = LLMProviderRouter(primary=primary, fallback=fallback)

    try:
        router.generate("question", {})
    except LLMAdapterError:
        pass

    assert primary.calls == 1
    assert fallback.calls == 1
