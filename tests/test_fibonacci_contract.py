from types import SimpleNamespace

import engine.fibonacci_engine as fib


def _candles():
    candles = [
        {
            "high": 110.0,
            "low": 105.0,
            "close": 108.0,
            "volume": 1.0,
        }
        for _ in range(100)
    ]

    candles[20]["high"] = 121.0
    candles[70]["low"] = 100.0
    candles[-1]["close"] = 111.0

    return candles


def _run(monkeypatch, price=111.0):
    candles = _candles()

    monkeypatch.setattr(
        fib,
        "get_candles",
        lambda state: candles,
    )
    monkeypatch.setattr(
        fib,
        "valid_candles",
        lambda data: data,
    )

    return fib.analyze(SimpleNamespace(price=price))


def test_retracements_and_extensions_are_separate(monkeypatch):
    result = _run(monkeypatch)
    metadata = result["metadata"]

    assert list(metadata["retracements"]) == [
        "0.0",
        "23.6",
        "38.2",
        "50.0",
        "61.8",
        "78.6",
        "100.0",
    ]

    assert list(metadata["extensions"]) == [
        "127.2",
        "161.8",
        "261.8",
    ]

    assert "261.8" not in metadata["retracements"]
    assert "261.8" in metadata["extensions"]


def test_extension_ratios_are_exact(monkeypatch):
    result = _run(monkeypatch)
    extensions = result["metadata"]["extensions"]

    assert extensions["127.2"] == 126.71
    assert extensions["161.8"] == 133.98
    assert extensions["261.8"] == 154.98


def test_38_2_to_50_zone_is_premium(monkeypatch):
    result = _run(monkeypatch)

    assert result["metadata"]["zone"] == "PREMIUM"
    assert "PREMIUM" in result["reasons"]
    assert "DISCOUNT" not in result["reasons"]
