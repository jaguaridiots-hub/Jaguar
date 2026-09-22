import json

from market.nse_provider import NSEProvider, NSEProviderError


def _payload(symbol="RELIANCE.NS"):
    # Six valid 15m candles + one Yahoo quote/placeholder row.
    timestamps = [
        1789708500,
        1789709400,
        1789710300,
        1789711200,
        1789712100,
        1789713000,
        1789713280,  # deliberately not 15m-aligned
    ]

    quote = {
        "open":   [1238, 1239, 1240, 1241, 1242, 1243, 1243],
        "high":   [1239, 1240, 1241, 1242, 1243, 1244, 1243],
        "low":    [1237, 1238, 1239, 1240, 1241, 1242, 1243],
        "close":  [1238.5, 1239.5, 1240.5, 1241.5, 1242.5, 1243.5, 1243],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 0],
    }

    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": symbol,
                        "dataGranularity": "15m",
                    },
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [quote],
                    },
                }
            ],
            "error": None,
        }
    }


class _FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


def _fake_opener(request, timeout=15):
    return _FakeResponse(_payload())


def test_nse_provider_returns_canonical_15m_candles():
    provider = NSEProvider(opener=_fake_opener)

    candles = provider.load(
        "RELIANCE.NS",
        interval="15m",
        limit=300,
    )

    assert candles
    assert len(candles) == 6

    required = {
        "time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    assert set(candles[0]) == required

    for candle in candles:
        assert candle["time"] % 900_000 == 0
        assert candle["close_time"] == candle["time"] + 900_000
        assert candle["volume"] > 0
        assert candle["high"] >= max(
            candle["open"],
            candle["close"],
        )
        assert candle["low"] <= min(
            candle["open"],
            candle["close"],
        )


def test_nse_provider_preserves_symbol_identity():
    provider = NSEProvider(opener=_fake_opener)

    candles = provider.load("TCS.NS", interval="15m", limit=300)

    assert candles
    assert all(isinstance(candle, dict) for candle in candles)


def test_nse_provider_rejects_non_nse_symbol():
    provider = NSEProvider(opener=_fake_opener)

    try:
        provider.load("BTCUSDT", interval="15m", limit=300)
    except NSEProviderError:
        return

    raise AssertionError("NSE provider accepted a non-NSE symbol")


def test_nse_provider_rejects_unsupported_interval():
    provider = NSEProvider(opener=_fake_opener)

    try:
        provider.load("RELIANCE.NS", interval="1m", limit=300)
    except NSEProviderError:
        return

    raise AssertionError("Unsupported NSE interval was accepted")


if __name__ == "__main__":
    test_nse_provider_returns_canonical_15m_candles()
    test_nse_provider_preserves_symbol_identity()
    test_nse_provider_rejects_non_nse_symbol()
    test_nse_provider_rejects_unsupported_interval()
    print("NSE_PROVIDER_CONTRACT: PASS")
